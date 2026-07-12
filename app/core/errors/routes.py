from flask import render_template
from app.core.utils.blueprints import make_blueprint

errors_bp = make_blueprint("errors", __name__, __file__, url_prefix=None)


def register_error_handlers(app):
    @app.errorhandler(404)
    @app.errorhandler(403)
    @app.errorhandler(500)
    def handle_error(e):
        code = getattr(e, "code", 500)
        return render_template(errors_bp.get_templates_path(f"{code}.html")), code