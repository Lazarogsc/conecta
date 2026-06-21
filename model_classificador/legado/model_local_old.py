import joblib
import re
import os
from ia.preprocess import clean_text

# ===== Carregar Pipeline ANTIGO (snapshot v3.0 extraído do git) =====
pipeline_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline_old.pkl")
try:
    pipeline = joblib.load(pipeline_path)
except FileNotFoundError:
    pipeline = None  # Evita erro fatal se o train_model não rodar antes

# ══════════════════════════════════════════════════════════════════════
# 🔒 CAMADA 1 — BLOQUEIO DETERMINÍSTICO (REGEX)
# ══════════════════════════════════════════════════════════════════════

# Termos que SEMPRE resultam em "adulto", mesmo com variações morfológicas.
# Usamos raízes (stems) + regex para pegar flexões: puta, putas, putaria, putona etc.

RAIZES_PROIBIDAS = [
    # Termos sexuais
    r"sex[ou]",           # sexo, sexu(al)
    r"porn[oô]?",         # porno, pornô, porn
    r"bucet[ai]",         # buceta, buceti(nha)
    r"pir[oô]c",          # piroca, pirocão
    r"xerec",             # xereca
    r"caralh",            # caralho, caralha
    r"put[aio]",          # puta, puto, puti(nho), putas, putaria
    r"putari",            # putaria
    r"fod[aeiou]",        # foda, foder, fodi, fodeu
    r"trepar",            # trepar
    r"goz[aei]",          # gozar, gozo, gozei
    r"orgasmo",           # orgasmo
    r"erot[ii]c",         # erótico, erotismo
    r"safad[aoi]",        # safado, safada
    r"tarad[aoi]",        # tarado, tarada
    r"bronh[ai]",         # bronha
    r"punhet",            # punheta
    r"boque",             # boquete
    r"chupar",            # chupar (sentido sexual)
    r"nud[ei]",           # nudez, nudes
    r"pelad[aoi]",        # pelado, pelada
    r"tesao",             # tesão
    r"tesud[aoi]",        # tesudo, tesuda
    r"motel",             # motel
    r"cabaret?e?",        # cabare, cabaré, cabaret
    r"striptease",        # striptease
    r"stripper",          # stripper
    r"fetiching?",        # fetiche
    r"fetich",            # fetiche
    r"masturb",           # masturbação, masturbar
    r"ejacul",            # ejacular, ejaculação
    r"orgias?",           # orgia, orgias
    r"swing",             # swing (sexual)
    r"menage",            # ménage
    r"cu[zs]a[oã]",       # cuzão
    r"rolud",             # roludo
    r"chifr",             # chifre, chifrud_
    r"corno",             # corno

    # Genitalias e corpo
    r"\bcu\b",            # cu (isolado)
    r"\bcus\b",           # cus
    r"rol[ao]",           # rola, rolão (sexual)
    r"p[eê]ni[sz]",       # penis, pênis
    r"vagin[ai]",         # vagina
    r"anus",              # ânus
    r"clitori",           # clitóris
    r"escroto",           # escroto (xingamento)

    # Drogas
    r"maconh[ai]",        # maconha
    r"cocain",            # cocaína, cocaina
    r"crack",             # crack
    r"heroina",           # heroína (droga)
    r"ecstasy",           # ecstasy
    r"metanfetamina",     # metanfetamina
    r"lsd",               # LSD
    r"cheirar\s*(po|coca|pó)",  # cheirar pó
    r"trafic",            # tráfico, traficante
    r"brisad[aoi]",       # brisado
    r"\bbeck\b",          # beck (maconha)
    r"\bbaseado\b",       # baseado (maconha)
    r"chapad[ao]",        # chapado, chapada

    # Violência extrema
    r"estupro",           # estupro
    r"estupr[aei]",       # estuprar, estuprei
    r"pedofil",           # pedofilia, pedófilo
    r"abus[aoe].*sexual", # abuso sexual
    r"abus[aoe].*menor",  # abuso de menor
    r"assassin",          # assassinar, assassinato
    r"suicid",            # suicídio
    r"automutil",         # automutilação

    # Xingamentos pesados
    r"vagabund[aoi]",     # vagabundo, vagabunda
    r"viad[aoi]",         # viado
    r"retardad[aoi]",     # retardado
    r"arrombad[aoi]",     # arrombado
    r"filh[aoi]\s*(da\s+)?put[aoi]", # filho da puta
    r"desgraçad[aoi]",    # desgraçado
    r"desgracad[aoi]",    # sem acento
    r"desgracad",         # variações
    r"lixo\s+human",      # lixo humano
    r"escori[ao]",        # escória
    r"nojent[aoi]",       # nojento
    r"imbecil",           # imbecil
    r"idiota",            # idiota
    r"cretino",           # cretino
    r"maldito",           # maldito
    r"miseravel",         # miserável
    r"babac[aã]",         # babaca
    r"otari[ao]",         # otário

    # Racismo / discriminação (Art. 20, ECA)
    r"negr[aoi]\s+fede",  # racismo
    r"macac[aoi]",        # macaco (racismo)
    r"neguinh[aoi]\s",    # racismo
    r"pretinha suja",     # racismo
    r"hitler",            # apologia nazismo
    r"nazist",            # apologia nazismo

    # Conteúdo perigoso para menores
    r"me\s+mand[aei]\s+nud",   # "me manda nudes"
    r"quero\s+ver\s+voc[eê]\s+pelad", # grooming
    r"vem\s+c[aá]\s+em\s+casa",       # grooming

    # Contexto sensual/sexual implícito (gírias)
    r"rebolar",           # rebolar, rebolando
    r"rebol[aei]",        # rebolei, rebola
    r"quic[aei]",         # quicar, quicando
    r"sent[aei]\s.*gost", # sentar gostoso
    r"sentad[aoi]",       # sentada, sentadão (sexual)
    r"gemend",            # gemendo
    r"gostos[aoi]",       # gostosa, gostoso (sexual)
    r"delici[aoi]",       # deliciosa (sexual)
    r"gatinha.*quero",    # "gatinha quero"
    r"quero.*gatinha",    # "quero gatinha"
    r"pegacao",           # pegação
    r"ficad[aoi]",        # ficada (sexual)
    r"peg[aei]r?\s+geral",# pegar geral
    r"chup[aei]",         # chupar, chupei
    r"mam[aei]r?\b",      # mamar (sexual)
    r"dar\s+(o|a)\s+cu",  # dar o cu
    r"com[eê]r?\s+(ela|ele|alguem)", # comer alguém (sexual)
    r"meter",             # meter (sexual)
    r"metend",            # metendo
    r"socand",            # socando (sexual)
    r"engolir\s+tud",     # engolir tudo
    r"lamber",            # lamber (sexual)
    r"lambend",           # lambendo
    r"devass[aoi]",       # devassa
    r"promiscu",          # promíscuo, promiscuidade
    r"surub[aoi]",        # suruba
    r"menage|manage",     # ménage
    r"gang\s*bang",       # gangbang
    r"sacanagem",         # sacanagem
    r"sacana",            # sacana
    r"tarad[aoi]",        # tarado
    r"assedi[aoi]",       # assédio
    r"abus[aoe]r?",       # abusar
    r"violentar",         # violentar
    r"espancar",          # espancar
    r"\bporra\b",         # porra
    r"\bmerda\b",         # merda
    r"\bcacete\b",        # cacete (xingamento)
    r"fdp",               # fdp (abreviação)
    r"vsf",               # vsf (abreviação)
    r"vtnc",              # vtnc (abreviação)
    r"pqp",               # pqp (abreviação)
]

# Compilar todos os patterns uma vez (performance)
_PATTERNS_PROIBIDOS = [re.compile(p, re.IGNORECASE) for p in RAIZES_PROIBIDAS]


# ══════════════════════════════════════════════════════════════════════
# 🔒 CAMADA 1 — BLOQUEIO DURO POR REGEX
# ══════════════════════════════════════════════════════════════════════

def bloqueio_explicito(texto):
    """
    Busca patterns proibidos no texto normalizado.
    Usa regex com raízes para pegar todas as flexões morfológicas.
    """
    for pattern in _PATTERNS_PROIBIDOS:
        if pattern.search(texto):
            return "adulto"
    return None


# ══════════════════════════════════════════════════════════════════════
# 🧠 CAMADA 2 — MODELO TF-IDF + LOGISTIC REGRESSION
# ══════════════════════════════════════════════════════════════════════

def modelo_estatistico(texto):
    """Classificação probabilística pelo modelo ML."""
    if not pipeline:
        return "neutro", 0.0  # Fallback caso falte o modelo

    probs = pipeline.predict_proba([texto])[0]
    classes = pipeline.classes_

    prob_adulto = probs[list(classes).index("adulto")]
    classe_predita = pipeline.predict([texto])[0]

    return classe_predita, prob_adulto


# ══════════════════════════════════════════════════════════════════════
# 🛡 CAMADA 3 — POLÍTICA CONSERVADORA (Custo-Sensível)
# ══════════════════════════════════════════════════════════════════════

def politica_conservadora(classe_predita, prob_adulto, threshold=0.35):
    """
    Se a probabilidade de adulto for > 35%, classifica como adulto.
    Threshold calibrado: baixo o suficiente para pegar conteúdo adulto
    disfarçado, alto o suficiente para não bloquear "Bom dia".
    """
    if prob_adulto > threshold:
        return "adulto"
    return classe_predita


# ══════════════════════════════════════════════════════════════════════
# 🚀 FUNÇÃO FINAL — Pipeline de 3 camadas
# ══════════════════════════════════════════════════════════════════════

def classificar_local(texto):
    """
    Pipeline de classificação de conteúdo em 3 camadas:
    
    1. PRÉ-PROCESSAMENTO: Anti-ofuscação (leetspeak, espaços, acentos, homoglyphs)
    2. CAMADA 1 - REGEX: Bloqueio determinístico por raízes morfológicas
    3. CAMADA 2 - ML: Classificação probabilística TF-IDF + Logistic Regression
    4. CAMADA 3 - POLÍTICA: Threshold conservador (30%) para proteger menores
    """
    # PRÉ-PROCESSAMENTO
    texto_limpo = clean_text(texto)

    # CAMADA 1 — Bloqueio determinístico
    resultado_bloqueio = bloqueio_explicito(texto_limpo)
    if resultado_bloqueio:
        return resultado_bloqueio

    # Também checar texto ORIGINAL (sem normalização) para pegar formatos incomuns
    resultado_original = bloqueio_explicito(texto.lower())
    if resultado_original:
        return resultado_original

    # CAMADA 2 — Modelo ML
    classe_predita, prob_adulto = modelo_estatistico(texto_limpo)

    # CAMADA 3 — Política conservadora
    return politica_conservadora(classe_predita, prob_adulto)