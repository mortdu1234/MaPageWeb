from flask import render_template
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

nombres_aleatoires_bp = make_blueprint("projet_nombres_aleatoires", __name__, __file__, url_prefix="/nombres-aleatoires")


@nombres_aleatoires_bp.route("/")
def index():
    # Les infos du header et de l'infobox viennent de static/json/header.json
    return render_template(
        nombres_aleatoires_bp.get_templates_path("projet_nombres_aleatoires.html"),
        project=load_header(nombres_aleatoires_bp),
    )
