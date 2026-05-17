from flask import render_template
from routes import require_permission
from routes.games import jeux_bp

@jeux_bp.route("/ptitBac")
@require_permission("showGame")
def ptitBac():
    return render_template("jeux/ptitBac.html")

@jeux_bp.route("/ptitBac/game")
@require_permission("showGame")
def ptitBac_game():
    return render_template("jeux/ptitBacGame.html")

@jeux_bp.route("/ptitBac/submit", methods=["POST"])
@require_permission("showGame")
def ptitBac_submit():
    return render_template("jeux/ptitBacSubmit.html")