from flask import render_template
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

etude_siem_bp = make_blueprint("projet_etude_siem", __name__, __file__, url_prefix="/etude-siem")


@etude_siem_bp.route("/")
def index():
    # Les infos du header et de l'infobox viennent de static/json/header.json
    return render_template(
        etude_siem_bp.get_templates_path("projet_etude_siem.html"),
        project=load_header(etude_siem_bp),
    )
