from flask import render_template
from app.core.utils.blueprints import make_blueprint

algorithmeGenetique_bp = make_blueprint("algorithmeGenetique", __name__, __file__, url_prefix="/projets/algorithmeGenetique")


@algorithmeGenetique_bp.route("/")
def page():
    return render_template(algorithmeGenetique_bp.get_templates_path("algorithmegenetique.html"))
