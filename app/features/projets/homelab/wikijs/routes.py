from flask import render_template, url_for
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

wikijs_bp = make_blueprint("projet_homelab_wikijs", __name__, __file__, url_prefix="/wikijs")


@wikijs_bp.route("/")
def index():
    # Les infos du header viennent de static/json/header.json
    return render_template(
        wikijs_bp.get_templates_path("projet_homelab_wikijs.html"),
        project=load_header(wikijs_bp),
        back_url=url_for("projets.projet_homelab.index"),
        back_label="← Retour au HomeLab",
        show_type=False,
    )
