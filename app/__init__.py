import os

import click
from flask import Flask, g, request

from app.config import CONFIGS
from app.extensions import db, migrate
from app.formatting import formatar_moeda
from app.i18n import METADADOS, resolver_idioma, traduzir, traduzir_plural, traduzir_secao
from app.preferences import Preferencias

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "migrations")


def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)

    config_name = config_name or os.environ.get("FLASK_CONFIG", "development")
    app.config.from_object(CONFIGS[config_name])
    if not app.config["SQLALCHEMY_DATABASE_URI"]:
        os.makedirs(app.instance_path, exist_ok=True)
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(app.instance_path, "menu.db")

    db.init_app(app)
    # Caminho absoluto: as migrations funcionam de qualquer diretório de trabalho.
    migrate.init_app(app, db, directory=MIGRATIONS_DIR)

    _registrar_blueprints(app)
    _registrar_contexto(app)
    _registrar_cli(app)

    if app.config["AUTO_INIT_DB"]:
        with app.app_context():
            _inicializar_banco()

    return app


def _registrar_blueprints(app):
    from app.routes.menu import menu_bp
    from app.routes.preferencias import preferencias_bp
    from app.routes.qrcode import qrcode_bp

    app.register_blueprint(menu_bp)
    app.register_blueprint(preferencias_bp)
    app.register_blueprint(qrcode_bp)


def _registrar_contexto(app):
    @app.before_request
    def carregar_preferencias():
        cookie = request.cookies.get(app.config["PREFS_COOKIE_NAME"])
        g.prefs = Preferencias.from_cookie(cookie, app.config["IDIOMAS"])
        g.idioma = resolver_idioma(g.prefs.idioma)

    @app.context_processor
    def injetar_globais():
        lang_html, lang_voz, _ = METADADOS[g.idioma]
        return {
            "t": traduzir,
            "tp": traduzir_plural,
            "ts": traduzir_secao,
            "prefs": g.prefs,
            "idioma": g.idioma,
            "lang_html": lang_html,
            "lang_voz": lang_voz,
            "idiomas": [(codigo, METADADOS[codigo][2]) for codigo in app.config["IDIOMAS"]],
        }

    @app.template_filter("moeda")
    def filtro_moeda(valor):
        return formatar_moeda(valor, g.idioma)


def _inicializar_banco():
    """Aplica as migrations pendentes e popula o banco se estiver vazio."""
    from flask_migrate import upgrade

    from app.seed import seed_if_empty

    upgrade(directory=MIGRATIONS_DIR)
    return seed_if_empty()


def _registrar_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Aplica as migrations e popula com dados de exemplo se o banco estiver vazio."""
        criado = _inicializar_banco()
        click.echo("Banco criado e populado." if criado else "Banco já possui dados; nada a fazer.")

    @app.cli.command("seed")
    def seed():
        """Popula um banco vazio (já migrado) com dados de exemplo."""
        from app.seed import seed_if_empty

        click.echo("Dados de exemplo inseridos." if seed_if_empty() else "Banco já possui dados.")
