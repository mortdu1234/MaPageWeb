from flask import render_template
from routes.auth import require_permission
from routes.games import jeux_bp

@jeux_bp.route("/ptitbac")
@require_permission("showGame")
def ptitbac():
    return render_template("jeux/ptitbac.html")
