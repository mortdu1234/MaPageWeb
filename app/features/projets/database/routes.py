from flask import render_template
from app.core.utils.blueprints import make_blueprint

database_bp = make_blueprint("database", __name__, __file__, url_prefix="/projets/database")


@database_bp.route("/")
def page():
    return render_template(database_bp.get_templates_path("database.html"))
