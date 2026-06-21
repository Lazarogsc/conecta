# Conecta — Protótipo Web de Classificação Textual de Conteúdo Impróprio

Protótipo web de rede social que utiliza Inteligência Artificial para classificar
automaticamente publicações textuais nas categorias **adulto**, **infantil** ou
**neutro**, filtrando o conteúdo conforme a faixa etária dos usuários como apoio à
**proteção infantil online**.

> Este repositório acompanha o Trabalho de Conclusão de Curso intitulado
> *"Conecta: Protótipo Web de Classificação Textual de Conteúdo Impróprio para Apoio
> à Proteção Infantil Online"*. Trata-se de um **protótipo acadêmico e experimental**,
> não de um produto pronto para produção.

---

## Objetivo acadêmico

Investigar como uma moderação textual **organizada em camadas**, combinando regras
determinísticas e aprendizado de máquina, pode reduzir a exposição de menores a
conteúdos adultos em ambientes digitais, priorizando a **revocação (recall)** da
classe adulta — isto é, minimizando os falsos negativos (conteúdo adulto exibido
indevidamente a menores), ainda que ao custo de alguns falsos positivos.

A meta metodológica definida no trabalho é **recall ≥ 85%** para a classe adulta.

## Funcionalidades

- Cadastro e login de usuários, com senhas protegidas por **bcrypt**.
- Validação de senha forte no cadastro (boas práticas de segurança).
- Feed de publicações em ordem cronológica reversa.
- Criação de publicações e comentários textuais.
- **Filtragem por faixa etária**: para perfis menores de 18 anos, publicações
  classificadas como adultas são bloqueadas na publicação e ocultadas do feed e da busca.
- Moderação automática de publicações **e** comentários/respostas.
- Interações sociais: seguir/deixar de seguir, perfis privados com solicitação,
  curtidas, comentários aninhados e notificações.
- Acessibilidade básica (diretrizes WCAG 2.1 AA: HTML semântico, navegação por teclado,
  contraste, textos alternativos).

## Tecnologias

| Camada            | Tecnologia                                  |
|-------------------|---------------------------------------------|
| Backend           | Python 3.12, Flask                          |
| ORM / Banco       | SQLAlchemy, Flask-SQLAlchemy, SQLite        |
| Autenticação      | Flask-Login, Flask-Bcrypt (bcrypt)          |
| Templates         | Jinja2, HTML5, CSS3, JavaScript             |
| IA / Classificação| scikit-learn (TF-IDF + Regressão Logística), NumPy, Pandas, Joblib |
| Configuração      | python-dotenv (.env)                        |
| Avaliação (TCC)   | matplotlib, seaborn, statsmodels            |

## Arquitetura

Arquitetura **monolítica** dividida em três camadas lógicas, conforme descrito na
monografia (Cap. 4):

- **Apresentação** — templates HTML5 renderizados pelo Jinja2, com CSS3 e JavaScript.
- **Aplicação** — backend Flask em `app.py`, concentrando rotas, sessão, acesso ao
  banco e a chamada ao módulo de classificação.
- **Módulo de IA** — isolado no pacote `ia/`, acionado a cada novo texto submetido.

## O classificador híbrido (3 camadas)

A função de entrada é `ia.model_local.classificar_local(texto)`:

1. **Pré-processamento anti-ofuscação** (`ia/preprocess.py` → `clean_text`):
   normaliza o texto neutralizando *leetspeak* (`s3x0` → `sexo`), letras espaçadas
   (`s e x o` → `sexo`), *homoglyphs*, acentos, emojis e repetições excessivas.
2. **Camada 1 — Bloqueio determinístico (Regex):** termos inequivocamente impróprios
   (sexual explícito, drogas pesadas, aliciamento) resultam imediatamente na classe
   `adulto`, sem custo de inferência.
3. **Camada 2 — TF-IDF + Regressão Logística:** vetorização TF-IDF (unigramas e
   bigramas) e classificador linear que produz a probabilidade de cada classe.
4. **Camada 3 — Política conservadora:** classifica como `adulto` quando a
   probabilidade estimada supera o limiar calibrado por validação cruzada
   (`threshold_adulto = 0.51`, em `pipeline_meta.json`).

## Estrutura de pastas

```
model_classificador/
├── app.py                  # Aplicação Flask (rotas + modelos + moderação)
├── config.py               # Configuração via variáveis de ambiente (.env)
├── requirements.txt        # Dependências
├── .env.example            # Modelo de variáveis de ambiente
├── ia/                     # Módulo de classificação textual
│   ├── preprocess.py       # clean_text (anti-ofuscação)
│   └── model_local.py      # Pipeline de 3 camadas
├── templates/              # Páginas HTML (Jinja2)
├── static/                 # CSS, JS, imagens
├── pipeline.pkl            # Modelo treinado (TF-IDF + Reg. Logística)
├── pipeline_meta.json      # Metadados do modelo (limiar calibrado, métricas)
├── train_model.py          # Dataset + treinamento + calibração do limiar
├── populate_db.py          # Popular o banco com dados de demonstração
├── reset_db.py             # Recriar o banco do zero
├── avaliar_modelos.py      # Avaliação estatística (Tabela 1, McNemar, ROC, PR)
├── simular_ambiente.py     # Validação em ambiente simulado (Tabela 2)
├── dados_simulacao.py      # Corpus sintético da simulação (405 publicações)
├── legado/                 # Classificador da versão anterior (baseline de comparação)
├── graficos_tcc/           # Figuras geradas para o TCC
└── tests/                  # Testes automatizados (pytest)
```

## Como executar

Pré-requisito: **Python 3.12**.

```bash
# 1. Criar e ativar um ambiente virtual
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# 2. Instalar as dependências
pip install -r requirements.txt

# 3. Configurar as variáveis de ambiente
#    Copie o .env.example para .env e ajuste a SECRET_KEY
cp .env.example .env

# 4. (Opcional) Popular o banco com dados de demonstração
python populate_db.py

# 5. Executar o servidor
python app.py
```

A aplicação ficará disponível em `http://127.0.0.1:5000`.

> O banco SQLite (`database.db`) é criado automaticamente na primeira execução.
> Para recriá-lo do zero: `python reset_db.py`.

## Treinamento e avaliação do modelo

O modelo já vem treinado em `pipeline.pkl`. Para reproduzir o treinamento e a avaliação:

```bash
# Treinar o modelo e recalibrar o limiar (gera pipeline.pkl e pipeline_meta.json)
python train_model.py

# Avaliação estatística: comparação de algoritmos (Tabela 1),
# Teste de McNemar, curvas ROC e Precision-Recall, matriz de confusão
python avaliar_modelos.py

# Validação em ambiente simulado (Tabela 2): 405 publicações sintéticas
python simular_ambiente.py
```

### Conjunto de dados

O dataset de treinamento é **sintético** (466 textos rotulados: 154 adulto, 132
infantil, 180 neutro), redigido para fins acadêmicos. O corpus de simulação
(`dados_simulacao.py`) também é sintético. Nenhum dado pessoal real é utilizado.

## Testes

```bash
pip install pytest
pytest -v
```

Os testes cobrem o pré-processamento anti-ofuscação, a camada de bloqueio por regex
e a classificação nas três classes. Os testes das classes infantil/neutro exigem o
`pipeline.pkl` treinado (são pulados automaticamente se o modelo não existir).

## Segurança

- Senhas armazenadas com hash **bcrypt** (nunca em texto puro).
- `SECRET_KEY` e demais segredos lidos de variáveis de ambiente (`.env`), fora do
  código-fonte.
- Consultas parametrizadas via SQLAlchemy (mitiga injeção de SQL).
- Escape automático do Jinja2 nos templates (mitiga XSS).
- Rotas sensíveis protegidas por autenticação (`@login_required`).
- Controle de acesso por faixa etária para proteção de menores.

## Limitações

- Ausência de validação com usuários reais em produção.
- Dataset de treinamento e de simulação de natureza **sintética**, concebidos pelo
  próprio autor (risco de viés de confirmação — discutido na monografia).
- Sem múltiplos anotadores independentes (*Inter-Rater Reliability*).
- Moderação restrita a **texto** (sem imagens, vídeos ou áudios).
- Idade autodeclarada pelo usuário.
- Risco residual de falsos positivos e falsos negativos; revisão humana ainda
  necessária para casos ambíguos.

## Autoria

- **Autor:** Lázaro Geiel Sousa Costa
- **Orientadora:** Profa. Dra. Lianna Mara Castro Duarte
- **Curso:** Bacharelado em Ciência da Computação
- **Instituição:** Universidade Estadual do Piauí (UESPI) — CTU
- **Ano:** 2026
