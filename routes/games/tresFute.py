from flask import render_template
from routes.auth import require_permission
from routes.games import jeux_bp

@jeux_bp.route("/tresfute")
@require_permission("showGame")
def tresfute():
    return render_template("jeux/tresfute.html")