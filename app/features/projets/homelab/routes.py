from flask import render_template
from app.core.utils.blueprints import make_blueprint

homelab_bp = make_blueprint("homelab", __name__, __file__, url_prefix="/projets/homelab")


@homelab_bp.route("/")
def page():
    return render_template(homelab_bp.get_templates_path("server.html"))
