from flask import render_template
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

castle_clash_2048_bp = make_blueprint("projet_castle_clash_2048", __name__, __file__, url_prefix="/castle-clash-2048")


@castle_clash_2048_bp.route("/")
def index():
    # Les infos du header et de l'infobox viennent de static/json/header.json
    return render_template(
        castle_clash_2048_bp.get_templates_path("projet_castle_clash_2048.html"),
        project=load_header(castle_clash_2048_bp),
    )
