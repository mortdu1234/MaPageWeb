"""
routes/auth.py
Gestion de l'authentification : login, register, logout.
Toutes les interactions BDD passent par db/users.py et db/permissions.py.
"""

from flask import Blueprint, render_template, request, redirect, url_for, abort
from functools import wraps

from db.users import get_user_by_username, get_user_by_id, username_exists, create_user, verify_password
from db.permissions import get_user_permissions
from sessionUser import SessionUser


auth_bp = Blueprint("auth", __name__)


# ─── Revalidation BDD ─────────────────────────────────────────────────────────

def _revalidate_user() -> list[str] | None:
    """
    Recharge les permissions depuis la BDD à chaque requête sensible.
    Retourne la liste des permissions, ou None si le compte n'existe plus.
    """
    user_id = SessionUser.user_id()
    if not user_id:
        return None
    if not get_user_by_id(user_id):
        return None  # Compte supprimé → session invalide
    return get_user_permissions(user_id)


# ─── Décorateurs ──────────────────────────────────────────────────────────────

def login_required(f):
    """Redirige vers /login si l'utilisateur n'est pas connecté."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not SessionUser.is_logged_in():
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def require_permission(perm_name):
    """
    Vérifie la permission EN BASE à chaque appel.
    Déconnecte si le compte a été supprimé, renvoie 403 si permission absente.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not SessionUser.is_logged_in():
                return redirect(url_for("auth.login"))

            perms = _revalidate_user()

            if perms is None:
                SessionUser.logout()
                return redirect(url_for("auth.login"))

            if "admin" not in perms and perm_name not in perms:
                abort(403)

            return f(*args, **kwargs)
        return decorated
    return decorator


# ─── Routes ───────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if SessionUser.is_logged_in():
        return redirect(url_for("main.index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            error = "Tous les champs sont obligatoires."
        else:
            try:
                user = get_user_by_username(username)
                if user and verify_password(password, user[2]):
                    perms = get_user_permissions(user[0])
                    SessionUser.login(user, perms)
                    return redirect(url_for("main.index"))
                else:
                    error = "Identifiants incorrects."
            except Exception as e:
                error = "Erreur de connexion à la base de données."
                print(f"[AUTH] Login error: {e}")

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

        if not username or not password:
            error = "Tous les champs sont obligatoires."
        elif len(username) < 3:
            error = "Le nom d'utilisateur doit faire au moins 3 caractères."
        elif len(password) < 8:
            error = "Le mot de passe doit faire au moins 8 caractères."
        elif password != password_confirm:
            error = "Les mots de passe ne correspondent pas."
        else:
            try:
                if username_exists(username):
                    error = "Ce nom d'utilisateur est déjà pris."
                else:
                    create_user(username, password)
                    return redirect(url_for("auth.login"))
            except Exception as e:
                error = "Erreur de connexion à la base de données."
                print(f"[AUTH] Register error: {e}")

    return render_template("register.html", error=error)


@auth_bp.route("/logout")
def logout():
    SessionUser.logout()
    return redirect(url_for("main.index"))