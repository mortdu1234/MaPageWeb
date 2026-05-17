from flask import Blueprint, render_template, abort, jsonify
from routes import require_permission
from db.joueurs import get_all_joueurs

jeux_bp = Blueprint("jeux", __name__)

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

@jeux_bp.route("/players", methods=["GET"])
@require_permission("showGame")
def players():
    return jsonify(get_all_joueurs())

from routes.games import oanami, ptitBac, qwirkle, smileLife, trainMexicain, tresFute, triomino