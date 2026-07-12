"""
routes/auth.py
Gestion des routes d'authentification
"""

from flask import render_template, request, redirect, url_for

from .backend.auth import Auth
from ..utils.sessionUser import SessionUser

from app.core.utils.blueprints import make_blueprint

auth_bp = make_blueprint("auth", __name__, __file__, url_prefix=None)


# ─── Routes ───────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if SessionUser.is_logged_in():
        return redirect(url_for("index.index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        success, error = Auth.login(username, password)
        if success:
            return redirect(url_for("index.index"))

    return render_template(auth_bp.get_templates_path("login.html"), error=error)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if SessionUser.is_logged_in():
        return redirect(url_for("index.index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        success, error = Auth.register(username, password, password_confirm)

        if success:
            return redirect(url_for("auth.login"))

    return render_template(auth_bp.get_templates_path("register.html"), error=error)


@auth_bp.route("/logout")
def logout():
    SessionUser.logout()
    return redirect(url_for("index.index"))