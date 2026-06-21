import os

from dotenv import load_dotenv

# Carrega variáveis de ambiente definidas no arquivo .env (se existir).
# A chave de assinatura das sessões e demais segredos ficam fora do código-fonte,
# conforme o princípio de segurança discutido na monografia (Art. 46 da LGPD).
load_dotenv()

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    """Configuração central do protótipo Conecta.

    Os valores sensíveis são lidos de variáveis de ambiente. Em desenvolvimento,
    caso a variável não esteja definida, é usado um valor padrão apenas para que
    o protótipo continue executável; em uso real, defina SECRET_KEY no arquivo .env.
    """

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-troque-no-env")

    # Banco SQLite embarcado (caminho absoluto para funcionar a partir de qualquer cwd).
    _default_db = "sqlite:///" + os.path.join(_BASE_DIR, "database.db")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", _default_db)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Controla o modo debug do Flask. Por padrão desligado (seguro);
    # ative definindo FLASK_DEBUG=1 no ambiente de desenvolvimento.
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
