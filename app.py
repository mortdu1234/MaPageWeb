from flask import Flask, render_template
from config import Config
from sessionUser import SessionUser
from db import init_pool
from datetime import date


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    init_pool() 

    # Enregistrement des blueprints
    from routes.main import main_bp
    from routes.games import jeux_bp
    from routes.projets import projets_bp
    from routes.auth import auth_bp
    from routes.games.joueurs import joueurs_bp
    from routes.database import api_db_bp
    from routes.tasks import tasks_bp
    from routes.rsaKeys import rsaKeys_bp
    from routes.files import files_bp
    from routes.terminal import terminal_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(jeux_bp, url_prefix="/jeux")
    app.register_blueprint(projets_bp, url_prefix="/projets")
    app.register_blueprint(auth_bp)
    app.register_blueprint(joueurs_bp)
    app.register_blueprint(api_db_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(rsaKeys_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(terminal_bp)

    @app.context_processor
    def inject_user():
        return {
            "current_user": {
                "is_logged_in": SessionUser.is_logged_in(),
                "username":     SessionUser.username(),
                "is_admin":     SessionUser.is_admin(),
                "permissions":  SessionUser.permissions(),
            }
        }
    
    @app.context_processor
    def inject_today():
        return {"today": date.today().isoformat()}

    
    # ─── Gestionnaires d'erreurs ──────────────────────────────────────────────

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=25555)