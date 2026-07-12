from flask import render_template
from app.core.utils.routesHelper import require_permission
from app.core.utils.blueprints import make_blueprint

boardGame_smileLife_bp = make_blueprint("boardgame-smileLife", __name__, __file__, "/jeux/smileLife")

@boardGame_smileLife_bp.route("/")
@require_permission("showGame")
def page():
    return render_template(boardGame_smileLife_bp.get_templates_path("smileLife.html"))

@boardGame_smileLife_bp.route("/game")
@require_permission("showGame")
def smileLife_game():
    return render_template(boardGame_smileLife_bp.get_templates_path("smileLifeGame.html"))

@boardGame_smileLife_bp.route("/submit", methods=["POST"])
@require_permission("showGame")
def smileLife_submit():
    return render_template(boardGame_smileLife_bp.get_templates_path("smileLifeSubmit.html"))