from flask import render_template
from routes import require_permission
from routes.games import jeux_bp

@jeux_bp.route("/triomino")
@require_permission("showGame")
def triomino():
    return render_template("jeux/triomino.html")

@jeux_bp.route("/triomino/game")
@require_permission("showGame")
def triomino_game():
    return render_template("jeux/triominoGame.html")

@jeux_bp.route("/triomino/submit", methods=["POST"])
@require_permission("showGame")
def triomino_submit():
    return render_template("jeux/triominoSubmit.html")