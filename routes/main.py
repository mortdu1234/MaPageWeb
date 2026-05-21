from flask import Blueprint, render_template
from routes import require_permission

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/apropos")
def apropos():
    return render_template("apropos.html")


@main_bp.route("/contact")
def contact():
    return render_template("contact.html")

@main_bp.route("/tasks")
def tasks():
    return render_template("tasks.html")
