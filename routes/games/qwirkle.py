from flask import render_template
from routes.auth import require_permission
from routes.games import jeux_bp

@jeux_bp.route("/qwirkle")
@require_permission("showGame")
def qwirkle():
    return render_template("jeux/qwirkle.html")