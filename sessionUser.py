from flask import session


class SessionUser:
    """Encapsule la session Flask pour un accès propre aux données utilisateur."""

    # ─── Écriture (login) ─────────────────────────────────────────────────────

    @staticmethod
    def login(user_row, permissions):
        """
        À appeler après vérification du mot de passe.
        user_row : tuple issu du SELECT (id, username, is_admin)
        permissions : liste de strings ['voir_jeux', 'voir_projets', ...]
        """
        session["user_id"]     = user_row[0]
        session["username"]    = user_row[1]
        session["permissions"] = permissions
        session["is_admin"]    = "admin" in permissions

    @staticmethod
    def logout():
        session.clear()

    # ─── Lecture ──────────────────────────────────────────────────────────────

    @staticmethod
    def is_logged_in():
        return "user_id" in session

    @staticmethod
    def user_id():
        return session.get("user_id")

    @staticmethod
    def username():
        return session.get("username")

    @staticmethod
    def is_admin():
        return session.get("is_admin")

    @staticmethod
    def permissions():
        return session.get("permissions", [])

    @staticmethod
    def has_permission(perm_name):
        if SessionUser.is_admin():
            return True
        return perm_name in SessionUser.permissions()

    # ─── Modification ─────────────────────────────────────────────────────────

    @staticmethod
    def set(key, value):
        session[key] = value

    @staticmethod
    def get(key, default=None):
        return session.get(key, default)