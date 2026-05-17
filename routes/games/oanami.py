from flask import render_template
from routes import require_permission
from routes.games import jeux_bp


@jeux_bp.route("/oanami")
@require_permission("showGame")
def oanami():
    return render_template("jeux/oanami.html")

@jeux_bp.route("/oanami/game")
@require_permission("showGame")
def oanami_game():
    return render_template("jeux/oanamiGame.html")

@jeux_bp.route("/oanami/submit", methods=["POST"])
@require_permission("showGame")
def oanami_submit():
    return render_template("jeux/oanamiSubmit.html")