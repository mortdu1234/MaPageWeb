from flask import render_template
from app.core.utils.blueprints import make_blueprint

nginx_bp = make_blueprint("nginx", __name__, __file__, url_prefix="/projets/nginx")


@nginx_bp.route("/")
def page():
    return render_template(nginx_bp.get_templates_path("nginx.html"))
