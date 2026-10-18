from flask import render_template
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

loup_garou_bp = make_blueprint("projet_loup_garou", __name__, __file__, url_prefix="/loup-garou")


@loup_garou_bp.route("/")
def index():
    # Les infos du header et de l'infobox viennent de static/json/header.json
    return render_template(
        loup_garou_bp.get_templates_path("projet_loup_garou.html"),
        project=load_header(loup_garou_bp),
    )
