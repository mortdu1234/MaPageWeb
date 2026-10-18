from flask import render_template, url_for
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

gaming_bp = make_blueprint("projet_homelab_gaming", __name__, __file__, url_prefix="/gaming")


@gaming_bp.route("/")
def index():
    # Les infos du header viennent de static/json/header.json
    return render_template(
        gaming_bp.get_templates_path("projet_homelab_gaming.html"),
        project=load_header(gaming_bp),
        back_url=url_for("projets.projet_homelab.index"),
        back_label="← Retour au HomeLab",
        show_type=False,
    )
