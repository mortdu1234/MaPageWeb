from flask import render_template
from app.core.utils.routesHelper import require_permission
from app.core.utils.blueprints import make_blueprint

trainMexicain_bp = make_blueprint("trainMexicain", __name__, __file__, "/jeux/trainMexicain")

@trainMexicain_bp.route("/")
@require_permission("showGame")
def page():
    return render_template(trainMexicain_bp.get_templates_path("trainMexicain.html"))

@trainMexicain_bp.route("/game")
@require_permission("showGame")
def trainMexicain_game():
    return render_template(trainMexicain_bp.get_templates_path("trainMexicainGame.html"))

@trainMexicain_bp.route("/submit", methods=["POST"])
@require_permission("showGame")
def trainMexicain_submit():
    return render_template(trainMexicain_bp.get_templates_path("trainMexicainSubmit.html"))