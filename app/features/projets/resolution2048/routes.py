from flask import render_template
from app.core.utils.blueprints import make_blueprint

resolution2048_bp = make_blueprint("resolution2048", __name__, __file__, url_prefix="/projets/resolution2048")


@resolution2048_bp.route("/")
def page():
    return render_template(resolution2048_bp.get_templates_path("resolution2048.html"))
