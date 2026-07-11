from flask import render_template, request, jsonify

from app.core.utils.blueprints import make_blueprint

apropos_bp = make_blueprint("apropos", __name__, url_prefix=None)


@apropos_bp.route("/apropos")
def apropos():
    return render_template("apropos.html")

