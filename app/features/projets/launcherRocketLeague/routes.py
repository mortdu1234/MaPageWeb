# app/features/projets/launcherRocketLeague/routes.py
from flask import render_template
from app.core.utils.blueprints import make_blueprint

launcher_bp = make_blueprint("launcherrocketleague", __name__, __file__, url_prefix="/projets/launcherrocketleague")

@launcher_bp.route("/")
def page():
    return render_template(launcher_bp.get_templates_path("launcherrocketleague.html"))