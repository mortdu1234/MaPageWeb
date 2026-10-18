from flask import render_template
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

rsa_aes_bp = make_blueprint("projet_rsa_aes", __name__, __file__, url_prefix="/rsa-aes")


@rsa_aes_bp.route("/")
def index():
    # Les infos du header et de l'infobox viennent de static/json/header.json
    return render_template(
        rsa_aes_bp.get_templates_path("projet_rsa_aes.html"),
        project=load_header(rsa_aes_bp),
    )
