from flask import render_template
from app.core.utils.routesHelper import require_permission
from app.core.utils.blueprints import make_blueprint

qwirkle_bp = make_blueprint("qwirkle", __name__, __file__, "/jeux/qwirkle")

@qwirkle_bp.route("/")
@require_permission("showGame")
def page():
    return render_template(qwirkle_bp.get_templates_path("qwirkle.html"))

@qwirkle_bp.route("/game")
@require_permission("showGame")
def qwirkle_game():
    return render_template(qwirkle_bp.get_templates_path("qwirkleGame.html"))

@qwirkle_bp.route("/submit", methods=["POST"])
@require_permission("showGame")
def qwirkle_submit():
    return render_template(qwirkle_bp.get_templates_path("qwirkleSubmit.html"))