from flask import render_template
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

algo_genetique_bp = make_blueprint("projet_algo_genetique", __name__, __file__, url_prefix="/algorithme-genetique")


@algo_genetique_bp.route("/")
def index():
    # Les infos du header et de l'infobox viennent de static/json/header.json
    return render_template(
        algo_genetique_bp.get_templates_path("projet_algo_genetique.html"),
        project=load_header(algo_genetique_bp),
    )
