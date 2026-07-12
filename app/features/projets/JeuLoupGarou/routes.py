from flask import render_template
from app.core.utils.blueprints import make_blueprint

jeuLoupGarou_bp = make_blueprint("jeuLoupGarou", __name__, __file__, url_prefix="/projets/JeuLoupGarou")


@jeuLoupGarou_bp.route("/")
def page():
    return render_template(jeuLoupGarou_bp.get_templates_path("jeuloupgarou.html"))
