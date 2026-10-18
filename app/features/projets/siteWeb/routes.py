from flask import render_template
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

site_web_bp = make_blueprint("projet_site_web", __name__, __file__, url_prefix="/site-web")


@site_web_bp.route("/")
def index():
    # Les infos du header et de l'infobox viennent de static/json/header.json
    return render_template(
        site_web_bp.get_templates_path("projet_site_web.html"),
        project=load_header(site_web_bp),
    )
