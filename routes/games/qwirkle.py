from flask import render_template
from routes.auth import require_permission
from routes.games import jeux_bp

@jeux_bp.route("/qwirkle")
@require_permission("showGame")
def qwirkle():
    return render_template("jeux/qwirkle.html")

@jeux_bp.route("/qwirkle/game")
@require_permission("showGame")
def qwirkle_game():
    return render_template("jeux/qwirkleGame.html")

@jeux_bp.route("/qwirkle/submit", methods=["POST"])
@require_permission("showGame")
def qwirkle_submit():
    return render_template("jeux/qwirkleSubmit.html")