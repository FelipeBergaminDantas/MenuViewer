"""Configurações por ambiente.

Valores sensíveis ou específicos do deploy vêm de variáveis de ambiente,
para que o mesmo código rode em dev, teste e produção sem alterações.
"""

import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-inseguro-troque-em-producao")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")  # None -> SQLite em instance/
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # URL pública usada no QR Code (ex.: https://cardapio.meurestaurante.com.br/).
    # Se vazia, o QR aponta para a URL da requisição atual.
    PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "")

    # Idiomas disponíveis na interface; o primeiro é o padrão.
    IDIOMAS = ("pt", "en", "es")

    # Cria as tabelas e popula com dados de exemplo ao subir o app, se o banco
    # estiver vazio. Útil em desenvolvimento; em produção use `flask db upgrade`.
    AUTO_INIT_DB = False

    PREFS_COOKIE_NAME = "prefs"
    PREFS_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 ano
    PREFS_COOKIE_SECURE = False


class DevelopmentConfig(Config):
    DEBUG = True
    AUTO_INIT_DB = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    PREFS_COOKIE_SECURE = True


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
