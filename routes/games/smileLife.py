from flask import render_template
from routes.auth import require_permission
from routes.games import jeux_bp

@jeux_bp.route("/smileLife")
@require_permission("showGame")
def smileLife():
    return render_template("jeux/smileLife.html")

@jeux_bp.route("/smileLife/game")
@require_permission("showGame")
def smileLife_game():
    return render_template("jeux/smileLifeGame.html")

@jeux_bp.route("/smileLife/submit", methods=["POST"])
@require_permission("showGame")
def smileLife_submit():
    return render_template("jeux/smileLifeSubmit.html")