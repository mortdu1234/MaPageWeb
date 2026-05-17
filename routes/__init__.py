# Routes package

from flask import redirect, url_for, abort
from functools import wraps
from db.users import get_user_by_id
from db.permissions import get_user_permissions

from sessionUser import SessionUser

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
