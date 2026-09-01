import os

from flask import Flask

from app.database import db


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "menu.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)

    from app.routes.menu import menu_bp

    app.register_blueprint(menu_bp)

    with app.app_context():
        db.create_all()
        from app.seed import seed_if_empty

        seed_if_empty()

    return app
