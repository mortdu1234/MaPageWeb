"""
db/tasks.py
Toutes les requêtes SQL liées aux tables `tasks`, `task_shares`,
`task_groups` et `group_shares`.

Règles d'accès :
  - Seul le propriétaire (owner_id) peut créer, supprimer une tâche et gérer ses partages.
  - Un utilisateur avec permission 'write' peut toggler done et changer le groupe.
  - Un utilisateur avec permission 'read' peut seulement voir la tâche.
  - Les groupes appartiennent toujours à leur créateur (owner_id).
  - Un groupe peut être partagé ; ses tâches deviennent alors visibles
    pour les destinataires selon la permission du partage.
"""

from db import get_db, release_db


# ─── Helpers internes ─────────────────────────────────────────────────────────

def _row_to_task(row, permission: str, is_owner: bool) -> dict:
    # row : id, owner_id, text, done, created_at, group_id
    return {
        "id":         row[0],
        "owner_id":   row[1],
        "text":       row[2],
        "done":       bool(row[3]),
        "created_at": row[4].isoformat() if row[4] else None,
        "group_id":   row[5],
        "permission": permission,   # 'owner' | 'read' | 'write'
        "is_owner":   is_owner,
        "shared_with": [],          # rempli séparément pour les owners
    }


def _row_to_group(row, permission: str = "owner", is_owner: bool = True) -> dict:
    # row : id, owner_id, name, color, position, created_at
    return {
        "id":          row[0],
        "owner_id":    row[1],
        "name":        row[2],
        "color":       row[3],
        "position":    row[4],
        "created_at":  row[5].isoformat() if row[5] else None,
        "permission":  permission,   # 'owner' | 'read' | 'write'
        "is_owner":    is_owner,
        "shared_with": [],           # rempli séparément pour les owners
    }


def _ensure_utf8(conn) -> None:
    """Force l'encodage client UTF-8 sur la connexion."""
    cur = conn.cursor()
    cur.execute("SET client_encoding TO 'UTF8'")
    cur.close()


# ─── Lecture ──────────────────────────────────────────────────────────────────

def get_tasks_for_user(user_id: int) -> list[dict]:
    """
    Retourne toutes les tâches visibles par user_id :
      - tâches dont il est propriétaire
      - tâches partagées directement avec lui (task_shares)
      - tâches appartenant à un groupe partagé avec lui (group_shares)
    Chaque tâche inclut :
      - is_owner    : bool
      - permission  : 'owner' | 'read' | 'write'
      - shared_with : liste des {user_id, username, permission} (owners uniquement)
      - group_id    : int | None
    """
    conn = get_db()
    try:
        _ensure_utf8(conn)
        cur = conn.cursor()

        # DISTINCT ON (t.id) évite les doublons quand une tâche est accessible
        # à la fois via task_shares ET via group_shares.
        # Priorité : owner > task_share > group_share
        cur.execute("""
            SELECT * FROM (
                SELECT DISTINCT ON (t.id)
                       t.id, t.owner_id, t.text, t.done, t.created_at, t.group_id,
                       CASE
                           WHEN t.owner_id = %(uid)s        THEN 'owner'
                           WHEN ts.user_id IS NOT NULL      THEN ts.permission
                           ELSE gs.permission
                       END AS permission
                FROM tasks t
                LEFT JOIN task_shares  ts ON ts.task_id  = t.id       AND ts.user_id  = %(uid)s
                LEFT JOIN group_shares gs ON gs.group_id = t.group_id  AND gs.user_id  = %(uid)s
                WHERE t.owner_id = %(uid)s
                   OR ts.task_id  IS NOT NULL
                   OR gs.group_id IS NOT NULL
                ORDER BY t.id
            ) sub
            ORDER BY sub.created_at DESC
        """, {"uid": user_id})

        rows = cur.fetchall()
        tasks = []
        for row in rows:
            perm     = row[6]
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
        _ensure_utf8(conn)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, owner_id, text, done, created_at, group_id FROM tasks WHERE id = %s",
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
    Retourne True si user_id peut modifier la tâche
    (owner OU permission 'write' directe OU groupe partagé 'write').
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT 1 FROM tasks WHERE id = %s AND owner_id = %s
            UNION
            SELECT 1 FROM task_shares
             WHERE task_id = %s AND user_id = %s AND permission = 'write'
            UNION
            SELECT 1 FROM tasks t
             JOIN group_shares gs ON gs.group_id = t.group_id
            WHERE t.id = %s AND gs.user_id = %s AND gs.permission = 'write'
        """, (task_id, user_id, task_id, user_id, task_id, user_id))
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

def create_task(owner_id: int, text: str, group_id: int | None = None) -> dict:
    """Crée une tâche. Retourne la tâche créée complète."""
    conn = get_db()
    try:
        _ensure_utf8(conn)
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO tasks (owner_id, text, group_id)
               VALUES (%s, %s, %s)
               RETURNING id, owner_id, text, done, created_at, group_id""",
            (owner_id, text.strip(), group_id)
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


def set_task_group(task_id: int, group_id: int | None) -> bool:
    """
    Assigne (ou retire) un groupe à une tâche.
    Retourne True si la tâche a été trouvée et mise à jour.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE tasks SET group_id = %s WHERE id = %s",
            (group_id, task_id)
        )
        updated = cur.rowcount > 0
        conn.commit()
        return updated
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


# ─── Partages de tâches ───────────────────────────────────────────────────────

def get_all_users_except(user_id: int) -> list[dict]:
    """
    Retourne tous les utilisateurs sauf user_id.
    Utilisé pour peupler les modales de partage.
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


# ─── Groupes ──────────────────────────────────────────────────────────────────

def get_groups_for_user(user_id: int) -> list[dict]:
    """
    Retourne tous les groupes visibles par user_id :
      - groupes dont il est propriétaire
      - groupes partagés avec lui via group_shares
    Chaque groupe inclut :
      - is_owner    : bool
      - permission  : 'owner' | 'read' | 'write'
      - shared_with : liste des {user_id, username, permission} (owners uniquement)
    """
    conn = get_db()
    try:
        _ensure_utf8(conn)
        cur = conn.cursor()
        cur.execute("""
            SELECT tg.id, tg.owner_id, tg.name, tg.color, tg.position, tg.created_at,
                   CASE
                       WHEN tg.owner_id = %(uid)s THEN 'owner'
                       ELSE gs.permission
                   END AS permission
            FROM task_groups tg
            LEFT JOIN group_shares gs ON gs.group_id = tg.id AND gs.user_id = %(uid)s
            WHERE tg.owner_id = %(uid)s OR gs.user_id = %(uid)s
            ORDER BY tg.position ASC, tg.created_at ASC
        """, {"uid": user_id})

        rows = cur.fetchall()
        result = []
        for row in rows:
            perm     = row[6]
            is_owner = (row[1] == user_id)
            result.append(_row_to_group(row, perm, is_owner))

        # Charger les shared_with pour les groupes dont l'user est propriétaire
        owner_group_ids = [g["id"] for g in result if g["is_owner"]]
        if owner_group_ids:
            cur.execute("""
                SELECT gs.group_id, gs.user_id, u.username, gs.permission
                FROM group_shares gs
                JOIN users u ON u.id = gs.user_id
                WHERE gs.group_id = ANY(%s)
                ORDER BY u.username ASC
            """, (owner_group_ids,))
            shares_by_group: dict[int, list] = {}
            for r in cur.fetchall():
                shares_by_group.setdefault(r[0], []).append({
                    "user_id":    r[1],
                    "username":   r[2],
                    "permission": r[3],
                })
            for g in result:
                if g["is_owner"]:
                    g["shared_with"] = shares_by_group.get(g["id"], [])

        return result
    finally:
        release_db(conn)


def create_group(owner_id: int, name: str, color: str = "#b89a6a") -> dict:
    """Crée un groupe. Retourne le groupe créé."""
    conn = get_db()
    try:
        _ensure_utf8(conn)
        cur = conn.cursor()
        # Position = max actuel + 1
        cur.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 FROM task_groups WHERE owner_id = %s",
            (owner_id,)
        )
        next_pos = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO task_groups (owner_id, name, color, position)
            VALUES (%s, %s, %s, %s)
            RETURNING id, owner_id, name, color, position, created_at
        """, (owner_id, name.strip(), color, next_pos))
        row = cur.fetchone()
        conn.commit()
        return _row_to_group(row, "owner", True)
    finally:
        release_db(conn)


def update_group(group_id: int, name: str | None = None, color: str | None = None) -> dict | None:
    """Met à jour le nom et/ou la couleur d'un groupe. Retourne le groupe mis à jour ou None."""
    if name is None and color is None:
        return None
    conn = get_db()
    try:
        _ensure_utf8(conn)
        cur = conn.cursor()
        parts, params = [], []
        if name is not None:
            parts.append("name = %s")
            params.append(name.strip())
        if color is not None:
            parts.append("color = %s")
            params.append(color)
        params.append(group_id)
        cur.execute(
            f"UPDATE task_groups SET {', '.join(parts)} WHERE id = %s "
            f"RETURNING id, owner_id, name, color, position, created_at",
            params
        )
        row = cur.fetchone()
        conn.commit()
        return _row_to_group(row, "owner", True) if row else None
    finally:
        release_db(conn)


def delete_group(group_id: int) -> bool:
    """
    Supprime un groupe. Les tâches du groupe voient leur group_id mis à NULL (ON DELETE SET NULL).
    Retourne True si supprimé.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM task_groups WHERE id = %s", (group_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    finally:
        release_db(conn)


def reorder_groups(owner_id: int, ordered_ids: list[int]) -> bool:
    """
    Met à jour la position de chaque groupe selon l'ordre fourni.
    ordered_ids : liste des group_id dans le nouvel ordre.
    Retourne True si tout s'est bien passé.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        for pos, gid in enumerate(ordered_ids):
            cur.execute(
                "UPDATE task_groups SET position = %s WHERE id = %s AND owner_id = %s",
                (pos, gid, owner_id)
            )
        conn.commit()
        return True
    finally:
        release_db(conn)


def group_belongs_to(group_id: int, user_id: int) -> bool:
    """Vérifie que le groupe appartient bien à user_id (ownership)."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM task_groups WHERE id = %s AND owner_id = %s",
            (group_id, user_id)
        )
        return cur.fetchone() is not None
    finally:
        release_db(conn)


def group_accessible_by(group_id: int, user_id: int) -> bool:
    """
    Retourne True si user_id peut utiliser ce groupe pour créer une tâche :
    il en est propriétaire OU il a une permission 'write' dessus.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT 1 FROM task_groups WHERE id = %s AND owner_id = %s
            UNION
            SELECT 1 FROM group_shares
             WHERE group_id = %s AND user_id = %s AND permission = 'write'
        """, (group_id, user_id, group_id, user_id))
        return cur.fetchone() is not None
    finally:
        release_db(conn)


# ─── Partages de groupes ──────────────────────────────────────────────────────

def get_group_shares(group_id: int) -> list[dict]:
    """Retourne la liste des partages d'un groupe."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT gs.user_id, u.username, gs.permission
            FROM group_shares gs
            JOIN users u ON u.id = gs.user_id
            WHERE gs.group_id = %s
            ORDER BY u.username ASC
        """, (group_id,))
        return [{"user_id": r[0], "username": r[1], "permission": r[2]}
                for r in cur.fetchall()]
    finally:
        release_db(conn)


def share_group(group_id: int, target_user_id: int, permission: str = "read") -> bool:
    """
    Partage un groupe avec target_user_id.
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
            INSERT INTO group_shares (group_id, user_id, permission)
            VALUES (%s, %s, %s)
            ON CONFLICT (group_id, user_id)
            DO UPDATE SET permission = EXCLUDED.permission
        """, (group_id, target_user_id, permission))
        conn.commit()
        return True
    finally:
        release_db(conn)


def unshare_group(group_id: int, target_user_id: int) -> bool:
    """Retire le partage d'un groupe pour target_user_id. Retourne True si supprimé."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM group_shares WHERE group_id = %s AND user_id = %s",
            (group_id, target_user_id)
        )
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    finally:
        release_db(conn)