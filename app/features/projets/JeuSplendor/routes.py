from flask import render_template
from app.core.utils.blueprints import make_blueprint

jeuSplendor_bp = make_blueprint("jeuSplendor", __name__, __file__, url_prefix="/projets/JeuSplendor")


@jeuSplendor_bp.route("/")
def page():
    return render_template(jeuSplendor_bp.get_templates_path("jeusplendor.html"))
