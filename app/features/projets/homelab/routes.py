from flask import render_template
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

homelab_bp = make_blueprint("projet_homelab", __name__, __file__, url_prefix="/homelab")


@homelab_bp.route("/")
def index():
    # Les infos du header et de l'infobox viennent de static/json/header.json
    return render_template(
        homelab_bp.get_templates_path("projet_homelab.html"),
        project=load_header(homelab_bp),
    )
