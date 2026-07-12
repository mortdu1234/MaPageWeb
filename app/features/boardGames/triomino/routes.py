from flask import render_template
from app.core.utils.routesHelper import require_permission
from app.core.utils.blueprints import make_blueprint

triomino_bp = make_blueprint("triomino", __name__, __file__, "/jeux/triomino")

@triomino_bp.route("/")
@require_permission("showGame")
def page():
    return render_template(triomino_bp.get_templates_path("triomino.html"))

@triomino_bp.route("/game")
@require_permission("showGame")
def triomino_game():
    return render_template(triomino_bp.get_templates_path("triominoGame.html"))

@triomino_bp.route("/submit", methods=["POST"])
@require_permission("showGame")
def triomino_submit():
    return render_template(triomino_bp.get_templates_path("triominoSubmit.html"))