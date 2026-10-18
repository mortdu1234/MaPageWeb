"""
Application factory - version minimale.

Pas de base de données, pas de gestion d'utilisateurs pour le moment.
Juste Flask + enregistrement des blueprints.

Pour ajouter une feature : créer app/features/<nom>/routes.py avec un
blueprint via make_blueprint(...), puis l'ajouter à la liste ci-dessous.
"""

from flask import Flask
from types import SimpleNamespace
from app.core.utils.sessionUser import SessionUser
from .config import Config
from app.core.db.backend import init_pool

def create_app(config_class: type = Config) -> Flask:
    from .core.errors.routes import register_error_handlers
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_class)

    _register_blueprints(app)
    init_pool()

    register_error_handlers(app)

    @app.context_processor
    def inject_current_user():
        current_user = SimpleNamespace(
            username=SessionUser.username(),
            permissions=SessionUser.permissions(),
            is_admin=SessionUser.is_admin(),
            is_authenticated=SessionUser.is_logged_in(),
        )
        return dict(current_user=current_user)
    
    return app


def _register_blueprints(app: Flask) -> None:
    # ------ core ---------
    from .core.auth.routes import auth_bp
    from .core.crypto.routes import crypto_bp
    from .core.errors.routes import errors_bp
    
    # features
    from .features.boardGames.routes import jeux_bp
    from .features.dashboardProxmox.routes import proxmox_bp
    from .features.encryptFileTransfer.routes import files_bp
    from .features.serversGestion.routes import serverhub_bp
    from .features.serversGestion.minecraft.minigames.routes import serverMinijeux_bp
    from .features.tasksGestion.routes import tasks_bp
    from .features.projets.routes import projets_bp
    
    from .features.index.routes import index_bp
    from .features.apropos.routes import apropos_bp
    from .features.contact.routes import contact_bp

    from .features.boardGames.skyjo.routes import skyjo_bp
    from .features.boardGames.ohanami.routes import ohanami_bp
    from .features.boardGames.triomino.routes import triomino_bp
    from .features.boardGames.tresFute.routes import tresFute_bp
    from .features.boardGames.trainMexicain.routes import trainMexicain_bp
    from .features.boardGames.qwirkle.routes import qwirkle_bp
    from .features.boardGames.ptitBac.routes import ptitBac_bp
    from .features.boardGames.smileLife.routes import boardGame_smileLife_bp

    from .features.adminGestion.routes import permissions_bp
    from .features.GamesStatistiques.routes import stats_bp


    from .features.databaseReader.routes import db_reader_bp
    blueprints = [
        stats_bp,
        permissions_bp,
        skyjo_bp,
        ohanami_bp,triomino_bp,tresFute_bp,trainMexicain_bp,qwirkle_bp,ptitBac_bp,
        boardGame_smileLife_bp,db_reader_bp,
        index_bp,errors_bp,
        apropos_bp,
        contact_bp,
        auth_bp,
        crypto_bp,
        jeux_bp,
        projets_bp,
        proxmox_bp, 
        files_bp,
        serverhub_bp, 
        serverMinijeux_bp,
        tasks_bp 
        # ajoute ici tes autres blueprints au fur et à mesure
        # que tu les crées / répares
    ]

    for bp in blueprints:
        app.register_blueprint(bp)