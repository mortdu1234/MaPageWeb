# app/features/projets/launcherRocketLeague/routes.py
from flask import render_template
from app.core.utils.blueprints import make_blueprint

adSkipperDC_bp = make_blueprint("adSkipperDC", __name__, __file__, url_prefix="/projets/adSkipperDC")

@adSkipperDC_bp.route("/")
def page():
    return render_template(adSkipperDC_bp.get_templates_path("adskipperdc.html"))