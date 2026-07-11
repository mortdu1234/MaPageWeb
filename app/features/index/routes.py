from flask import render_template, request, jsonify

from app.core.utils.blueprints import make_blueprint

index_bp = make_blueprint("index", __name__, url_prefix=None)


@index_bp.route("/")
def index():
    return render_template("index.html")

