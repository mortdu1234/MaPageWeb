from flask import Blueprint, render_template, request, redirect, url_for
from routes import require_permission
from db.joueurs import create_joueur, joueur_exists

joueurs_bp = Blueprint("joueurs", __name__)


@joueurs_bp.route("/joueurs/nouveau", methods=["GET", "POST"])
@require_permission("showGame")
def nouveau_joueur():
    next_url = request.args.get("next") or request.form.get("next") or url_for("jeux.jeux")
    error    = None

    if request.method == "POST":
        prenom = request.form.get("prenom", "").strip()
        nom    = request.form.get("nom", "").strip()

        if not prenom or not nom:
            error = "Le prénom et le nom sont obligatoires."
        elif joueur_exists(prenom, nom):
            error = f"Le joueur « {prenom} {nom} » existe déjà."
        else:
            create_joueur(prenom, nom)
            return redirect(next_url)

    return render_template("nouveau.html", next_url=next_url, error=error)