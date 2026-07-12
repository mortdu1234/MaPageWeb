from flask import render_template
from app.core.utils.routesHelper import require_permission
from app.core.utils.blueprints import make_blueprint

tresFute_bp = make_blueprint("tresFute", __name__, __file__, "/jeux/tresFute")

@tresFute_bp.route("/")
@require_permission("showGame")
def page():
    return render_template(tresFute_bp.get_templates_path("tresFute.html"))

@tresFute_bp.route("/game")
@require_permission("showGame")
def tresFute_game():
    return render_template(tresFute_bp.get_templates_path("tresFuteGame.html"))

@tresFute_bp.route("/submit", methods=["POST"])
@require_permission("showGame")
def tresFute_submit():
    return render_template(tresFute_bp.get_templates_path("tresFuteSubmit.html"))