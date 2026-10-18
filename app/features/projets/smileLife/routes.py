from flask import render_template
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

smile_life_bp = make_blueprint("projet_smile_life", __name__, __file__, url_prefix="/smile-life")


@smile_life_bp.route("/")
def index():
    # Les infos du header et de l'infobox viennent de static/json/header.json
    return render_template(
        smile_life_bp.get_templates_path("projet_smile_life.html"),
        project=load_header(smile_life_bp),
    )
