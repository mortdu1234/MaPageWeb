from flask import Flask
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enregistrement des blueprints
    from routes.main import main_bp
    from routes.jeux import jeux_bp
    from routes.projets import projets_bp
    from routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(jeux_bp, url_prefix="/jeux")
    app.register_blueprint(projets_bp, url_prefix="/projets")
    app.register_blueprint(auth_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)