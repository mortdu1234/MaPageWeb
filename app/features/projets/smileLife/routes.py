from flask import render_template
from app.core.utils.blueprints import make_blueprint

smileLife_bp = make_blueprint("smileLife", __name__, __file__, url_prefix="/projets/smileLife")


@smileLife_bp.route("/")
def page():
    return render_template(smileLife_bp.get_templates_path("smilelife.html"))
