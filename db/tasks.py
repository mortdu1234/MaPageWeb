"""
db/tasks.py
Toutes les requêtes SQL liées aux tables `tasks` et `task_shares`.

Règles d'accès :
  - Seul le propriétaire (owner_id) peut créer, supprimer une tâche et gérer ses partages.
  - Un utilisateur avec permission 'write' peut toggler done.
  - Un utilisateur avec permission 'read' peut seulement voir la tâche.
"""

from db import get_db, release_db


# ─── Helpers internes ─────────────────────────────────────────────────────────

def _row_to_task(row, permission: str, is_owner: bool) -> dict:
    return {
        "id":         row[0],
        "owner_id":   row[1],
        "text":       row[2],
        "done":       row[3],
        "created_at": row[4].isoformat() if row[4] else None,
        "permission": permission,   # 'owner' | 'read' | 'write'
        "is_owner":   is_owner,
        "shared_with": [],          # rempli séparément pour les owners
    }


# ─── Lecture ──────────────────────────────────────────────────────────────────

def get_tasks_for_user(user_id: int) -> list[dict]:
    """
    Retourne toutes les tâches visibles par user_id :
      - tâches dont il est propriétaire
      - tâches partagées avec lui (read ou write)
    Chaque tâche inclut :
      - is_owner    : bool
      - permission  : 'owner' | 'read' | 'write'
      - shared_with : liste des {user_id, username, permission} (owners uniquement)
    """
    conn = get_db()
    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT t.id, t.owner_id, t.text, t.done, t.created_at,
                   CASE
                       WHEN t.owner_id = %(uid)s THEN 'owner'
                       ELSE ts.permission
                   END AS permission
            FROM tasks t
            LEFT JOIN task_shares ts ON ts.task_id = t.id AND ts.user_id = %(uid)s
            WHERE t.owner_id = %(uid)s OR ts.user_id = %(uid)s
            ORDER BY t.created_at DESC
        """, {"uid": user_id})

        rows = cur.fetchall()
        tasks = []
        for row in rows:
            perm     = row[5]
            is_owner = (row[1] == user_id)
            tasks.append(_row_to_task(row, perm, is_owner))

        # Pour les tâches dont l'user est propriétaire, charge les partages
        owner_task_ids = [t["id"] for t in tasks if t["is_owner"]]
        if owner_task_ids:
            cur.execute("""
                SELECT ts.task_id, ts.user_id, u.username, ts.permission
                FROM task_shares ts
                JOIN users u ON u.id = ts.user_id
                WHERE ts.task_id = ANY(%s)
                ORDER BY u.username ASC
            """, (owner_task_ids,))

            shares_by_task: dict[int, list] = {}
            for r in cur.fetchall():
                shares_by_task.setdefault(r[0], []).append({
                    "user_id":    r[1],
                    "username":   r[2],
                    "permission": r[3],
                })
            for t in tasks:
                if t["is_owner"]:
                    t["shared_with"] = shares_by_task.get(t["id"], [])

        return tasks
    finally:
        release_db(conn)


def get_task_by_id(task_id: int) -> dict | None:
    """Retourne une tâche brute par id, ou None."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, owner_id, text, done, created_at FROM tasks WHERE id = %s",
            (task_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return _row_to_task(row, "owner", True)
    finally:
        release_db(conn)


def user_can_write(task_id: int, user_id: int) -> bool:
    """
    Retourne True si user_id peut modifier la tâche (owner OU permission 'write').
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT 1 FROM tasks WHERE id = %s AND owner_id = %s
            UNION
            SELECT 1 FROM task_shares
            WHERE task_id = %s AND user_id = %s AND permission = 'write'
        """, (task_id, user_id, task_id, user_id))
        return cur.fetchone() is not None
    finally:
        release_db(conn)


def user_is_owner(task_id: int, user_id: int) -> bool:
    """Retourne True si user_id est propriétaire de la tâche."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM tasks WHERE id = %s AND owner_id = %s",
            (task_id, user_id)
        )
        return cur.fetchone() is not None
    finally:
        release_db(conn)


# ─── Écriture ─────────────────────────────────────────────────────────────────

def create_task(owner_id: int, text: str) -> dict:
    """Crée une tâche. Retourne la tâche créée complète."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO tasks (owner_id, text)
               VALUES (%s, %s)
               RETURNING id, owner_id, text, done, created_at""",
            (owner_id, text.strip())
        )
        row = cur.fetchone()
        conn.commit()
        return _row_to_task(row, "owner", True)
    finally:
        release_db(conn)


def toggle_task_done(task_id: int) -> bool | None:
    """
    Inverse l'état done d'une tâche.
    Retourne le nouvel état done, ou None si tâche introuvable.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE tasks SET done = NOT done WHERE id = %s RETURNING done",
            (task_id,)
        )
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
    finally:
        release_db(conn)


def delete_task(task_id: int) -> bool:
    """Supprime une tâche. Retourne True si supprimée."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    finally:
        release_db(conn)


# ─── Partages ─────────────────────────────────────────────────────────────────

def get_all_users_except(user_id: int) -> list[dict]:
    """
    Retourne tous les utilisateurs sauf user_id.
    Utilisé pour peupler la modale de partage.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username FROM users WHERE id != %s ORDER BY username ASC",
            (user_id,)
        )
        return [{"id": r[0], "username": r[1]} for r in cur.fetchall()]
    finally:
        release_db(conn)


def share_task(task_id: int, target_user_id: int, permission: str = "read") -> bool:
    """
    Partage une tâche avec target_user_id.
    Si le partage existe déjà, met à jour la permission.
    permission : 'read' | 'write'
    Retourne True si OK.
    """
    if permission not in ("read", "write"):
        return False
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO task_shares (task_id, user_id, permission)
            VALUES (%s, %s, %s)
            ON CONFLICT (task_id, user_id)
            DO UPDATE SET permission = EXCLUDED.permission
        """, (task_id, target_user_id, permission))
        conn.commit()
        return True
    finally:
        release_db(conn)


def unshare_task(task_id: int, target_user_id: int) -> bool:
    """Retire le partage d'une tâche pour target_user_id. Retourne True si supprimé."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM task_shares WHERE task_id = %s AND user_id = %s",
            (task_id, target_user_id)
        )
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    finally:
        release_db(conn)