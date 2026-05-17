from flask import render_template
from routes import require_permission
from routes.games import jeux_bp

@jeux_bp.route("/tresFute")
@require_permission("showGame")
def tresFute():
    return render_template("jeux/tresFute.html")

@jeux_bp.route("/tresFute/game")
@require_permission("showGame")
def tresFute_game():
    return render_template("jeux/tresFuteGame.html")

@jeux_bp.route("/tresFute/submit", methods=["POST"])
@require_permission("showGame")
def tresFute_submit():
    return render_template("jeux/tresFuteSubmit.html")