"""Routes d'authentification du package app."""

from flask import Blueprint, redirect, render_template, request, url_for

from app.core.auth.session import SessionUser
from app.core.auth.services import Auth

auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/auth/static",
)


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


__all__ = ["auth_bp"]
