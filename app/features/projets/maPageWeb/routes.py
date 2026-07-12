from flask import render_template
from app.core.utils.blueprints import make_blueprint

maPageWeb_bp = make_blueprint("maPageWeb", __name__, __file__, url_prefix="/projets/maPageWeb")


@maPageWeb_bp.route("/")
def page():
    return render_template(maPageWeb_bp.get_templates_path("mapageweb.html"))
