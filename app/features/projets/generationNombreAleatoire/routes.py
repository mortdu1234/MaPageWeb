from flask import render_template
from app.core.utils.blueprints import make_blueprint

generationNombreAleatoire_bp = make_blueprint("generationNombreAleatoire", __name__, __file__, url_prefix="/projets/generationNombreAleatoire")


@generationNombreAleatoire_bp.route("/")
def page():
    return render_template(generationNombreAleatoire_bp.get_templates_path("generationnombrealeatoire.html"))
