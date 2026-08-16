from flask import render_template, request, redirect, url_for, flash
from app.core.utils.routesHelper import require_permission, validate_json
from app.core.db.backend.parties import create_partie
from app.core.utils.blueprints import make_blueprint

skyjo_bp = make_blueprint("skyjo", __name__, __file__, "/jeux/skyjo")

def _int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default




@skyjo_bp.route("/")
@require_permission("showGame")
def page():
    return render_template(skyjo_bp.get_templates_path("skyjo.html"))


@skyjo_bp.route("/game")
@require_permission("showGame")
def skyjo_game():
    return render_template(skyjo_bp.get_templates_path("skyjoGame.html"))


@skyjo_bp.route("/submit", methods=["POST"])
@require_permission("showGame")
@validate_json("skyjo.json")
def skyjo_submit():
    return redirect(url_for("jeux.skyjo_game"))