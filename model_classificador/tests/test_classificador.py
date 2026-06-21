"""Testes do módulo de classificação textual do Conecta.

Cobrem as três camadas descritas na monografia (Cap. 4):
  - Pré-processamento anti-ofuscação (clean_text).
  - Camada 1: bloqueio determinístico por regex (bloqueio_explicito).
  - Pipeline completo (classificar_local) para as classes adulto/infantil/neutro.

Execução:
    pytest -v
"""
import pytest

from ia.preprocess import clean_text
from ia.model_local import bloqueio_explicito, classificar_local, pipeline


# ── Pré-processamento (anti-ofuscação) ──────────────────────────────────

def test_clean_text_lowercase_e_acentos():
    assert clean_text("COCAÍNA") == "cocaina"


def test_clean_text_leetspeak():
    # s3x0 -> sexo
    assert "sexo" in clean_text("s3x0")


def test_clean_text_letras_espacadas():
    # "s e x o" -> "sexo"
    assert "sexo" in clean_text("s e x o")


def test_clean_text_repeticao_excessiva():
    # caracteres repetidos em excesso são colapsados
    assert "sexo" in clean_text("seeeeexo")


def test_clean_text_entrada_invalida():
    assert clean_text(None) == ""


# ── Camada 1: bloqueio determinístico por regex ─────────────────────────

@pytest.mark.parametrize("texto", [
    "sexo",
    "pornografia",
    "maconha",
    "cocaina",
])
def test_bloqueio_explicito_detecta_termos_inequivocos(texto):
    assert bloqueio_explicito(clean_text(texto)) == "adulto"


def test_bloqueio_explicito_ignora_texto_inocente():
    assert bloqueio_explicito(clean_text("bom dia, vamos brincar no parque")) is None


# ── Pipeline completo de 3 camadas ──────────────────────────────────────

@pytest.mark.parametrize("texto", [
    "Conteudo sexual explicito para adultos",
    "Vamos fumar um beck de maconha",
    "s3x0 expl1c1to",  # ofuscado: precisa passar pela normalização
])
def test_classificar_local_adulto(texto):
    # A classe adulta é garantida pela Camada 1 (regex), independente do modelo.
    assert classificar_local(texto) == "adulto"


pipeline_indisponivel = pytest.mark.skipif(
    pipeline is None,
    reason="pipeline.pkl não encontrado; rode 'python train_model.py' antes.",
)


@pipeline_indisponivel
def test_classificar_local_infantil():
    assert classificar_local("Brincando no parque com os amigos da escola") == "infantil"


@pipeline_indisponivel
def test_classificar_local_neutro():
    assert classificar_local("Reunião de equipe sobre as metas do próximo trimestre") == "neutro"


@pipeline_indisponivel
def test_classificar_local_nunca_retorna_classe_invalida():
    classes_validas = {"adulto", "infantil", "neutro"}
    for texto in ["bom dia", "vamos estudar matematica", "cafe da manha"]:
        assert classificar_local(texto) in classes_validas
