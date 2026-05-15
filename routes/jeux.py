from flask import Blueprint, render_template, abort
from routes.auth import login_required, require_permission

jeux_bp = Blueprint("jeux", __name__)

# Liste des jeux disponibles
JEUX = [
    "oanami",
    "ptitbac",
    "qwirkle",
    "smilelife",
    "trainmexicain",
    "tresfute",
    "triomino",
]


@jeux_bp.route("/")
@require_permission("showGame")
def jeux():
    return render_template("jeux.html")


@jeux_bp.route("/<string:nom_jeu>")
@require_permission("showGame")
def detail_jeu(nom_jeu):
    if nom_jeu not in JEUX:
        abort(404)
    return render_template(f"jeux/{nom_jeu}.html")