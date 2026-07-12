from flask import render_template
from app.core.utils.routesHelper import require_permission
from app.core.utils.blueprints import make_blueprint

ptitBac_bp = make_blueprint("ptitBac", __name__, __file__, "/jeux/ptitBac")

@ptitBac_bp.route("/")
@require_permission("showGame")
def page():
    return render_template(ptitBac_bp.get_templates_path("ptitBac.html"))

@ptitBac_bp.route("/game")
@require_permission("showGame")
def ptitBac_game():
    return render_template(ptitBac_bp.get_templates_path("ptitBacGame.html"))

@ptitBac_bp.route("/submit", methods=["POST"])
@require_permission("showGame")
def ptitBac_submit():
    return render_template(ptitBac_bp.get_templates_path("ptitBacSubmit.html"))