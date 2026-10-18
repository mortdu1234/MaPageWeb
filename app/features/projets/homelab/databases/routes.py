from flask import render_template, url_for
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

databases_bp = make_blueprint("projet_homelab_databases", __name__, __file__, url_prefix="/databases")


@databases_bp.route("/")
def index():
    # Les infos du header viennent de static/json/header.json
    return render_template(
        databases_bp.get_templates_path("projet_homelab_databases.html"),
        project=load_header(databases_bp),
        back_url=url_for("projets.projet_homelab.index"),
        back_label="← Retour au HomeLab",
        show_type=False,
    )
