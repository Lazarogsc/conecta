import joblib
import re
import os
import json
from .preprocess import clean_text

# ══════════════════════════════════════════════════════════════════════
# CARREGAMENTO DO MODELO E DOS METADADOS
# ══════════════════════════════════════════════════════════════════════
_BASE = os.path.dirname(os.path.dirname(__file__))
pipeline_path = os.path.join(_BASE, "pipeline.pkl")
meta_path = os.path.join(_BASE, "pipeline_meta.json")

try:
    pipeline = joblib.load(pipeline_path)
except FileNotFoundError:
    pipeline = None  # Evita erro fatal se o train_model não rodar antes

# Limiar de decisão calibrado por validação cruzada (gravado por train_model.py
# em pipeline_meta.json). O valor calibrado reportado na monografia é 0,51;
# este default é apenas um fallback caso o arquivo de metadados não exista.
THRESHOLD_ADULTO = 0.51
try:
    with open(meta_path, "r", encoding="utf-8") as f:
        _meta = json.load(f)
        THRESHOLD_ADULTO = float(_meta.get("threshold_adulto", THRESHOLD_ADULTO))
except (FileNotFoundError, ValueError, KeyError):
    pass


# ══════════════════════════════════════════════════════════════════════
# CAMADA 1 — BLOQUEIO DETERMINÍSTICO (REGEX)
# ══════════════════════════════════════════════════════════════════════
#
# PRINCÍPIO DE PROJETO (revisão v4.0):
# A Camada 1 contém APENAS termos inequivocamente impróprios (NSFW), cuja
# presença, em qualquer contexto plausível de uma rede social, caracteriza
# conteúdo adulto. Termos ambíguos — que aparecem com frequência em textos
# inocentes (ex.: "gostoso", "delícia", "comer", "pelada" no sentido de
# futebol, "baseado" no sentido de "fundamentado", "macaco" como animal,
# xingamentos leves como "merda"/"idiota") — foram REMOVIDOS desta camada e
# delegados ao classificador estatístico (Camada 2). Essa separação foi a
# principal mudança para reduzir os falsos positivos observados na validação
# em ambiente simulado, sem comprometer a revocação da classe adulta, já que
# os termos verdadeiramente explícitos permanecem bloqueados de forma dura.
# ══════════════════════════════════════════════════════════════════════

RAIZES_PROIBIDAS = [
    # ── Sexual explícito (inequívoco) ──────────────────────────────────
    r"sex[ou]",            # sexo, sexual
    r"porn[oô]",           # porno, pornô, pornografia
    r"bucet[ai]",          # buceta
    r"xerec",              # xereca
    r"pir[oô]c",           # piroca
    r"caralh",             # caralho
    r"put[ao]\b",          # puta, puto (isolado)
    r"putari",             # putaria
    r"putinh",             # putinha
    r"fod[ae]r",           # foder, fodar
    r"fud[ae]r",           # fuder
    r"trepar",             # trepar (sexual)
    r"boquet",             # boquete
    r"punhet",             # punheta
    r"bronh[ai]",          # bronha
    r"siririca",           # siririca
    r"masturb",            # masturbação
    r"ejacul",             # ejaculação
    r"orgasmo",            # orgasmo
    r"er[oó]tic",          # erótico
    r"tes[ãa]o",           # tesão (desejo sexual explícito)
    r"safad[ao]\b",        # safada/safado (conotação sexual)
    r"pegac[ãa]o",         # pegação
    r"orgi[ao]",           # orgia
    r"surub[ao]",          # suruba
    r"m[eé]nage",          # ménage
    r"nudez",              # nudez
    r"\bnudes?\b",         # nudes / nude
    r"hentai",             # hentai
    r"onlyfans",           # onlyfans
    r"striptease",         # striptease
    r"stripper",           # stripper
    r"cabar[eé]",          # cabaré
    r"prostitu",           # prostituta, prostituição
    r"garota de programa", # garota de programa
    r"pedofil",            # pedofilia
    r"estupr",             # estupro, estuprar
    r"\bp[eê]nis\b",       # pênis
    r"\bvagina\b",         # vagina
    r"cl[ií]toris",        # clitóris
    r"\bgozada\b",         # gozada (sexual)

    # ── Drogas (termos inequívocos) ────────────────────────────────────
    r"maconh[ai]",         # maconha
    r"cocain",             # cocaína
    r"\bcrack\b",          # crack
    r"hero[ií]na",         # heroína
    r"ecstasy",            # ecstasy
    r"\blsd\b",            # LSD
    r"metanfetamina",      # metanfetamina
    r"\bbeck\b",           # beck (maconha)
    r"\bmd?ma\b",          # MDMA
    r"haxix",              # haxixe
    r"fum\w* (um |uns )?baseado",  # "fumar/fumando um baseado" (maconha)

    # ── Violência extrema / autolesão (inequívoco) ─────────────────────
    r"automutil",          # automutilação
    r"\bme matar\b",       # ideação suicida explícita

    # ── Aliciamento explícito (frases inequívocas) ─────────────────────
    r"me mand[aei]r? nud",       # "me manda nudes"
    r"manda(r)? (foto|fotos|video|videos) (sem roupa|pelad|intim|nud)",
    r"escondido dos? (seus? )?pais",  # "escondido dos seus pais"
    r"pack de nud",              # "pack de nudes"
    r"troc(ar)? nud",            # "trocar nudes"

    # ── Xingamentos sexuais pesados (compostos, baixa ambiguidade) ─────
    r"filh[ao] da put",          # filho/filha da puta
    r"vai (se |te )?(fod|fud)",  # "vai se foder"
    r"toma(r)? no cu",           # "tomar no cu"
    r"\bvtnc\b", r"\bvsf\b", r"\bfdp\b",  # abreviações ofensivas inequívocas
]

# Compilar todos os patterns uma vez (performance)
_PATTERNS_PROIBIDOS = [re.compile(p, re.IGNORECASE) for p in RAIZES_PROIBIDAS]


def bloqueio_explicito(texto):
    """Busca padrões inequivocamente impróprios no texto normalizado."""
    for pattern in _PATTERNS_PROIBIDOS:
        if pattern.search(texto):
            return "adulto"
    return None


# ══════════════════════════════════════════════════════════════════════
# CAMADA 2 — MODELO TF-IDF + CLASSIFICADOR LINEAR
# ══════════════════════════════════════════════════════════════════════

def modelo_estatistico(texto):
    """
    Classificação probabilística pelo modelo de ML.

    Retorna (classe_nao_adulta_mais_provavel, prob_adulto). A decisão sobre
    bloquear como "adulto" é tomada na Camada 3 com base no limiar; por isso
    aqui devolvemos sempre a melhor classe NÃO adulta como fallback, evitando
    que o argmax "adulto" (que em três classes pode ocorrer com probabilidade
    ~0,34) force o bloqueio independentemente do limiar calibrado.
    """
    if not pipeline:
        return "neutro", 0.0  # Fallback caso falte o modelo

    classes = list(pipeline.classes_)

    if hasattr(pipeline, "predict_proba"):
        probs = pipeline.predict_proba([texto])[0]
        prob_adulto = float(probs[classes.index("adulto")])
        # melhor classe entre as não adultas
        nao_adulto = [(probs[i], c) for i, c in enumerate(classes) if c != "adulto"]
        classe_fallback = max(nao_adulto)[1]
    else:
        classe_predita = pipeline.predict([texto])[0]
        prob_adulto = 1.0 if classe_predita == "adulto" else 0.0
        classe_fallback = classe_predita if classe_predita != "adulto" else "neutro"

    return classe_fallback, prob_adulto


# ══════════════════════════════════════════════════════════════════════
# CAMADA 3 — POLÍTICA CONSERVADORA (CUSTO-SENSÍVEL)
# ══════════════════════════════════════════════════════════════════════

def politica_conservadora(classe_predita, prob_adulto, threshold=None):
    """
    Classifica como adulto quando a probabilidade estimada supera o limiar
    calibrado por validação cruzada. O limiar foi elevado em relação à versão
    anterior (0,35 -> calibrado) justamente para reduzir falsos positivos,
    mantendo a revocação da classe adulta acima da meta de 85%.
    """
    if threshold is None:
        threshold = THRESHOLD_ADULTO
    if prob_adulto >= threshold:
        return "adulto"
    return classe_predita


# ══════════════════════════════════════════════════════════════════════
# FUNÇÃO FINAL — Pipeline de 3 camadas
# ══════════════════════════════════════════════════════════════════════

def classificar_local(texto, threshold=None):
    """
    Pipeline de classificação de conteúdo em três camadas:

    1. PRÉ-PROCESSAMENTO: anti-ofuscação (leetspeak, espaços, acentos, homoglyphs).
    2. CAMADA 1 — REGEX: bloqueio determinístico apenas de termos inequívocos.
    3. CAMADA 2 — ML: classificação probabilística (TF-IDF + modelo linear).
    4. CAMADA 3 — POLÍTICA: limiar calibrado por validação cruzada.
    """
    texto_limpo = clean_text(texto)

    # CAMADA 1 — Bloqueio determinístico (texto normalizado e original)
    if bloqueio_explicito(texto_limpo) or bloqueio_explicito(texto.lower()):
        return "adulto"

    # CAMADA 2 — Modelo ML
    classe_predita, prob_adulto = modelo_estatistico(texto_limpo)

    # CAMADA 3 — Política conservadora
    return politica_conservadora(classe_predita, prob_adulto, threshold)
