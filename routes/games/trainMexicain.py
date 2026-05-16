from flask import render_template
from routes.auth import require_permission
from routes.games import jeux_bp

@jeux_bp.route("/trainmexicain")
@require_permission("showGame")
def trainmexicain():
    return render_template("jeux/trainmexicain.html")