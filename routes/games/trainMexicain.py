from flask import render_template
from routes.auth import require_permission
from routes.games import jeux_bp

@jeux_bp.route("/trainMexicain")
@require_permission("showGame")
def trainmexicain():
    return render_template("jeux/trainMexicain.html")

@jeux_bp.route("/trainMexicain/game")
@require_permission("showGame")
def trainMexicain_game():
    return render_template("jeux/trainMexicainGame.html")

@jeux_bp.route("/trainMexicain/submit", methods=["POST"])
@require_permission("showGame")
def trainMexicain_submit():
    return render_template("jeux/trainMexicainSubmit.html")