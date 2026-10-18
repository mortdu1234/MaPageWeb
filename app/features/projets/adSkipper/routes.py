from flask import render_template
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

ad_skipper_bp = make_blueprint("projet_ad_skipper", __name__, __file__, url_prefix="/ad-skipper")


@ad_skipper_bp.route("/")
def index():
    # Les infos du header et de l'infobox viennent de static/json/header.json
    return render_template(
        ad_skipper_bp.get_templates_path("projet_ad_skipper.html"),
        project=load_header(ad_skipper_bp),
    )
