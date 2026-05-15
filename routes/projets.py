from flask import Blueprint, render_template, abort

projets_bp = Blueprint("projets", __name__)

# Liste des projets disponibles
PROJETS = [
    "addskipperdc",
    "algorithmegenetique",
    "generationnombrealeatoire",
    "jeuloupgarou",
    "jeusplendor",
    "launcherrocketleague",
    "resolution2048",
    "server",
    "serverminecraft",
    "smilelife",
    "vpn",
]


@projets_bp.route("/")
def mesprojets():
    return render_template("mesprojets.html")


@projets_bp.route("/<string:nom_projet>")
def detail_projet(nom_projet):
    if nom_projet not in PROJETS:
        abort(404)
    return render_template(f"projets/{nom_projet}.html")