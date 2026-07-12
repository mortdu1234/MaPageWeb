from flask import render_template
from app.core.utils.blueprints import make_blueprint

serversGaming_bp = make_blueprint("serversGaming", __name__, __file__, url_prefix="/projets/serversGaming")


@serversGaming_bp.route("/")
def page():
    return render_template(serversGaming_bp.get_templates_path("serverminecraft.html"))
