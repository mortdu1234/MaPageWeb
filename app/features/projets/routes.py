from flask import Blueprint, render_template, abort
from app.core.utils.blueprints import make_blueprint

projets_bp = make_blueprint("projets", __name__, __file__, url_prefix="/projets")


@projets_bp.route("/")
def mesprojets():
    return render_template(projets_bp.get_templates_path("hub.html"))
