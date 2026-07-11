from datetime import date

from flask import Flask

from app.config import Config
from app.core.auth import SessionUser
from app.extensions import init_extensions


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(config_class)
    init_extensions(app)

    from routes.main import main_bp
    from routes.games import jeux_bp
    from routes.projets import projets_bp
    from app.core.auth import auth_bp
    from routes.games.joueurs import joueurs_bp
    from routes.database import api_db_bp
    from app.features.tasks import tasks_bp
    from app.rsa_keys import rsaKeys_bp
    from app.features.files import files_bp
    from app.features.servers import proxmox_bp, serverhub_bp
    from app.core.errors import errors_bp
    from routes.games.serverMinijeux import serverMinijeux_bp

    app.register_blueprint(serverMinijeux_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(jeux_bp, url_prefix="/jeux")
    app.register_blueprint(projets_bp, url_prefix="/projets")
    app.register_blueprint(auth_bp)
    app.register_blueprint(joueurs_bp)
    app.register_blueprint(api_db_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(rsaKeys_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(errors_bp)
    app.register_blueprint(proxmox_bp)
    app.register_blueprint(serverhub_bp)

    @app.context_processor
    def inject_user():
        return {
            "current_user": {
                "is_logged_in": SessionUser.is_logged_in(),
                "username": SessionUser.username(),
                "is_admin": SessionUser.is_admin(),
                "permissions": SessionUser.permissions(),
            }
        }

    @app.context_processor
    def inject_today():
        return {"today": date.today().isoformat()}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", debug=True, port=25555)
