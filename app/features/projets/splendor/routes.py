from flask import render_template
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

splendor_bp = make_blueprint("projet_splendor", __name__, __file__, url_prefix="/splendor")


@splendor_bp.route("/")
def index():
    # Les infos du header et de l'infobox viennent de static/json/header.json
    return render_template(
        splendor_bp.get_templates_path("projet_splendor.html"),
        project=load_header(splendor_bp),
    )
