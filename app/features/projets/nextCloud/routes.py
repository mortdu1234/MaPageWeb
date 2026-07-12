from flask import render_template
from app.core.utils.blueprints import make_blueprint

nextCloud_bp = make_blueprint("nextCloud", __name__, __file__, url_prefix="/projets/nextCloud")


@nextCloud_bp.route("/")
def page():
    return render_template(nextCloud_bp.get_templates_path("nextcloud.html"))
