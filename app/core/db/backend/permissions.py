"""
db/permissions.py
Toutes les requêtes SQL liées aux tables `permissions` et `user_permissions`.
"""

from . import get_db, release_db


def get_user_permissions(user_id: int) -> list[str]:
    """
    Retourne la liste des noms de permissions d'un utilisateur.
    Ex : ['showGame', 'showProjet', 'admin']
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.name
            FROM user_permissions up
            JOIN permissions p ON p.id = up.permission_id
            WHERE up.user_id = %s
        """, (user_id,))
        return [row[0] for row in cur.fetchall()]
    finally:
        release_db(conn)


def get_all_permissions() -> list[dict]:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, description FROM permission ORDER BY name")
        rows = cur.fetchall()
        cur.close()
        return [{"id": r[0], "name": r[1], "description": r[2]} for r in rows]
    finally:
        release_db(conn)


def get_permissions_matrix():
    """
    Retourne (users, permissions, granted_set)
    - users : [{"id":..., "username":...}, ...]
    - permissions : [{"id":..., "name":..., "description":...}, ...]
    - granted_set : set of (user_id, permission_id) pour les droits déjà accordés
    """
    conn = get_db()
    try:
        cur = conn.cursor()

        cur.execute("SELECT id, username FROM users ORDER BY username")
        users = [{"id": r[0], "username": r[1]} for r in cur.fetchall()]

        cur.execute("SELECT id, name, description FROM permissions ORDER BY name")
        permissions = [{"id": r[0], "name": r[1], "description": r[2]} for r in cur.fetchall()]

        cur.execute("SELECT user_id, permission_id FROM user_permissions")
        granted_set = {(r[0], r[1]) for r in cur.fetchall()}

        cur.close()
        return users, permissions, granted_set
    finally:
        release_db(conn)


def grant_permission(user_id: int, permission_id: int, granted_by=None):
    """
    Ajoute le droit. Nécessite une contrainte UNIQUE (user_id, permission_id)
    sur la table user_permissions pour que ON CONFLICT fonctionne.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_permissions (user_id, permission_id, granted_by, granted_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (user_id, permission_id) DO NOTHING
        """, (user_id, permission_id, granted_by))
        conn.commit()
        cur.close()
    finally:
        release_db(conn)


def revoke_permission(user_id: int, permission_id: int):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM user_permissions
            WHERE user_id = %s AND permission_id = %s
        """, (user_id, permission_id))
        conn.commit()
        cur.close()
    finally:
        release_db(conn)