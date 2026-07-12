from flask import render_template
from app.core.utils.blueprints import make_blueprint

vpn_bp = make_blueprint("vpn", __name__, __file__, url_prefix="/projets/vpn")


@vpn_bp.route("/")
def page():
    return render_template(vpn_bp.get_templates_path("vpn.html"))
