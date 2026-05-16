from flask import render_template
from routes.auth import require_permission
from routes.games import jeux_bp

@jeux_bp.route("/smilelife")
@require_permission("showGame")
def smilelife():
    return render_template("jeux/smilelife.html")