from flask import Blueprint, render_template, abort, jsonify, request, url_for, redirect
from app.core.utils.routesHelper import require_permission
from app.core.db.backend.joueurs import get_all_joueurs
from app.core.auth.backend.auth import Auth
from app.core.utils.blueprints import make_blueprint

jeux_bp = make_blueprint("jeux", __name__, __file__, url_prefix="/jeux")


@jeux_bp.route("/")
@require_permission("showGame")
def jeux():
    return render_template(jeux_bp.get_templates_path("hub.html"))

@jeux_bp.route("/players", methods=["GET"])
@require_permission("showGame")
def players():
    return jsonify(get_all_joueurs())


@jeux_bp.route("/joueurs/nouveau", methods=["GET", "POST"])
@require_permission("showGame")
def nouveau_joueur():
    next_url = request.args.get("next") or request.form.get("next") or url_for("jeux.jeux")
    error    = None

    if request.method == "POST":
        prenom = request.form.get("prenom", "").strip()
        nom    = request.form.get("nom", "").strip()
        
        success, error = Auth.addNewPlayer(nom, prenom)
        if success:
            return redirect(next_url)

    return render_template(jeux_bp.get_templates_path("newPlayer.html"), next_url=next_url, error=error)