from flask import render_template
from routes.auth import require_permission
from routes.games import jeux_bp

@jeux_bp.route("/triomino")
@require_permission("showGame")
def triomino():
    return render_template("jeux/triomino.html")