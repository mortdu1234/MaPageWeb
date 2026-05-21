from flask import Blueprint, render_template

errors_bp = Blueprint("errors", __name__)

@errors_bp.errorhandler(404)
@errors_bp.errorhandler(403)
@errors_bp.errorhandler(500)
def handle_error(e):
    return render_template(f"errors/{e.code}.html")
