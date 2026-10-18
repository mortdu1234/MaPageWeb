from flask import render_template
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

rocket_league_launcher_bp = make_blueprint("projet_rocket_league_launcher", __name__, __file__, url_prefix="/rocket-league-launcher")


@rocket_league_launcher_bp.route("/")
def index():
    # Les infos du header et de l'infobox viennent de static/json/header.json
    return render_template(
        rocket_league_launcher_bp.get_templates_path("projet_rocket_league_launcher.html"),
        project=load_header(rocket_league_launcher_bp),
    )
