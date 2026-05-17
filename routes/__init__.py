# Routes package

from flask import redirect, url_for, abort, request, current_app
from functools import wraps
from db.users import get_user_by_id
from db.permissions import get_user_permissions

import json
import os
from jsonschema import validate, ValidationError

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


# ─── Chargement des schémas JSON ──────────────────────────────────────────────

_schema_cache: dict[str, dict] = {}

def _load_schema(file_name: str) -> dict:
    """
    Charge et met en cache un schéma JSON depuis static/json/.
    Lève une FileNotFoundError si le fichier est introuvable.
    """
    if file_name in _schema_cache:
        return _schema_cache[file_name]

    schema_path = os.path.join(current_app.root_path, "static", "json", file_name)

    if not os.path.isfile(schema_path):
        raise FileNotFoundError(f"Schéma JSON introuvable : {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    _schema_cache[file_name] = schema
    return schema


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

def validate_json(file_name: str):
    """
    Décorateur qui valide le corps JSON de la requête contre un schéma JSON Schema
    stocké dans static/json/<file_name>.

    Usage :
        @validate_json("oanami.json")
        def ma_route():
            ...

    Codes de retour :
        400 – corps non-JSON ou données invalides selon le schéma
        500 – fichier de schéma introuvable côté serveur
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 1. Chargement du schéma (avec cache)
            try:
                schema = _load_schema(file_name)
            except FileNotFoundError as e:
                current_app.logger.error(str(e))
                return {"error": "Schema file not found", "details": str(e)}, 500

            # 2. Parsing du corps de la requête
            data = request.get_json(silent=True)
            if data is None:
                return {"error": "Invalid JSON data", "details": "Le corps de la requête n'est pas du JSON valide."}, 400

            # 3. Validation contre le schéma
            try:
                validate(instance=data, schema=schema)
            except ValidationError as e:
                return {"error": "Invalid JSON data", "details": e.message}, 400

            return f(*args, **kwargs)
        return decorated
    return decorator