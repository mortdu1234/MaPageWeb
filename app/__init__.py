"""
Application factory - version minimale.

Pas de base de données, pas de gestion d'utilisateurs pour le moment.
Juste Flask + enregistrement des blueprints.

Pour ajouter une feature : créer app/features/<nom>/routes.py avec un
blueprint via make_blueprint(...), puis l'ajouter à la liste ci-dessous.
"""

from flask import Flask

from .config import Config


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_class)

    _register_blueprints(app)

    return app


def _register_blueprints(app: Flask) -> None:
    from .features.index.routes import index_bp
    from .features.apropos.routes import apropos_bp
    from .features.contact.routes import contact_bp

    blueprints = [
        index_bp,
        apropos_bp,
        contact_bp,
        # ajoute ici tes autres blueprints au fur et à mesure
        # que tu les crées / répares
    ]

    for bp in blueprints:
        app.register_blueprint(bp)