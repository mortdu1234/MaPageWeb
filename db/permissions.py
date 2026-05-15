"""
db/permissions.py
Toutes les requêtes SQL liées aux tables `permissions` et `user_permissions`.
"""

from db import get_db, release_db


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