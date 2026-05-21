from flask import Blueprint, render_template, request, redirect, url_for
from routes import require_permission
from backend.Auth import Auth

joueurs_bp = Blueprint("joueurs", __name__)


@joueurs_bp.route("/joueurs/nouveau", methods=["GET", "POST"])
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

    return render_template("nouveau.html", next_url=next_url, error=error)