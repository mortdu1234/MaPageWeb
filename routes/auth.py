"""
routes/auth.py
Gestion des routes d'authentification
"""

from flask import Blueprint, render_template, request, redirect, url_for

from backend.Auth import Auth
from sessionUser import SessionUser


auth_bp = Blueprint("auth", __name__)


# ─── Routes ───────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if SessionUser.is_logged_in():
        return redirect(url_for("main.index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        success, error = Auth.login(username, password)
        if success:
            return redirect(url_for("main.index"))

    return render_template("login.html", error=error)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if SessionUser.is_logged_in():
        return redirect(url_for("main.index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        success, error = Auth.register(username, password, password_confirm)

        if success:
            return redirect(url_for("auth.login"))

    return render_template("register.html", error=error)


@auth_bp.route("/logout")
def logout():
    SessionUser.logout()
    return redirect(url_for("main.index"))