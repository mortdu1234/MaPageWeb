"""
db/tasks.py
Schéma :
  tasks(id, name, is_done, group_id)
  tasks_groups(id, name, owner_id)
  shared_groups(group_id, allowed_for, allowed_by)
"""

from db import get_db, release_db


def db_get_tasks_and_groups(user_id: int) -> dict:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                t.id,
                t.name                       AS title,
                t.is_done,
                (tg.owner_id != %(uid)s)     AS is_shared,
                tg.id                        AS group_id,
                tg.name                      AS group_name
            FROM tasks t
            JOIN tasks_groups tg ON tg.id = t.group_id
            WHERE
                tg.owner_id = %(uid)s
                OR EXISTS (
                    SELECT 1 FROM shared_groups sg
                    WHERE sg.group_id    = tg.id
                    AND   sg.allowed_for = %(uid)s
                )
            ORDER BY t.id DESC
        """, {'uid': user_id})

        rows  = cur.fetchall()
        cols  = [d[0] for d in cur.description]
        tasks = [dict(zip(cols, row)) for row in rows]

        # Groupes propres + groupes partagés avec cet utilisateur
        cur.execute("""
            SELECT tg.id, tg.name
            FROM tasks_groups tg
            WHERE tg.owner_id = %(uid)s
            UNION
            SELECT tg.id, tg.name
            FROM tasks_groups tg
            JOIN shared_groups sg ON sg.group_id = tg.id
            WHERE sg.allowed_for = %(uid)s
            ORDER BY name
        """, {'uid': user_id})
        groups = [{'id': r[0], 'name': r[1]} for r in cur.fetchall()]

        cur.close()
        return {'tasks': tasks, 'groups': groups}
    finally:
        release_db(conn)


def db_create_task(title: str, group_id: int, owner_id: int) -> dict | None:
    """
    Crée une tâche dans `group_id`.
    Autorisé si `owner_id` est propriétaire du groupe OU si le groupe
    lui a été partagé via shared_groups.
    """
    conn = get_db()
    try:
        cur = conn.cursor()

        # Vérifie accès (propriétaire OU partagé) et récupère le nom du groupe
        cur.execute("""
            SELECT tg.id, tg.name, (tg.owner_id != %s) AS is_shared
            FROM tasks_groups tg
            WHERE tg.id = %s
              AND (
                  tg.owner_id = %s
                  OR EXISTS (
                      SELECT 1 FROM shared_groups sg
                      WHERE sg.group_id    = tg.id
                        AND sg.allowed_for = %s
                  )
              )
        """, (owner_id, group_id, owner_id, owner_id))
        group = cur.fetchone()

        if group is None:
            cur.close()
            return None

        group_db_id, group_name, is_shared = group

        cur.execute("""
            INSERT INTO tasks (name, is_done, group_id)
            VALUES (%s, FALSE, %s)
            RETURNING id
        """, (title, group_db_id))
        task_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return {
            'id':         task_id,
            'title':      title,
            'is_done':    False,
            'is_shared':  bool(is_shared),
            'group_id':   group_db_id,
            'group_name': group_name,
        }
    finally:
        release_db(conn)


def db_toggle_task(task_id: int, is_done: bool, user_id: int) -> bool:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE tasks
            SET is_done = %s
            WHERE id = %s
            AND (
                group_id IN (SELECT id FROM tasks_groups WHERE owner_id = %s)
                OR
                group_id IN (SELECT group_id FROM shared_groups WHERE allowed_for = %s)
            )
        """, (is_done, task_id, user_id, user_id))
        updated = cur.rowcount > 0
        conn.commit()
        cur.close()
        return updated
    finally:
        release_db(conn)


def db_delete_task(task_id: int, owner_id: int) -> bool:
    conn = get_db()
    try:
        cur = conn.cursor()
        # Permet la suppression si l'utilisateur a accès au groupe (propriétaire OU partagé)
        cur.execute("""
            DELETE FROM tasks
            WHERE id = %s
            AND group_id IN (
                SELECT tg.id FROM tasks_groups tg
                WHERE tg.owner_id = %s
                OR EXISTS (
                    SELECT 1 FROM shared_groups sg
                    WHERE sg.group_id = tg.id
                    AND sg.allowed_for = %s
                )
            )
        """, (task_id, owner_id, owner_id))
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        return deleted
    finally:
        release_db(conn)


def db_get_default_group(owner_id: int) -> dict | None:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name FROM tasks_groups
            WHERE owner_id = %s ORDER BY id ASC LIMIT 1
        """, (owner_id,))
        row = cur.fetchone()
        cur.close()
        return {'id': row[0], 'name': row[1]} if row else None
    finally:
        release_db(conn)


def db_create_group(name: str, owner_id: int) -> dict:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO tasks_groups (name, owner_id)
            VALUES (%s, %s) RETURNING id
        """, (name, owner_id))
        group_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return {'id': group_id, 'name': name}
    finally:
        release_db(conn)


def db_move_task(task_id: int, new_group_id: int, user_id: int) -> bool:
    conn = get_db()
    try:
        cur = conn.cursor()
        # Vérifie que l'utilisateur a accès au groupe destination (propriétaire OU partagé)
        cur.execute("""
            SELECT id FROM tasks_groups tg
            WHERE tg.id = %s
            AND (
                tg.owner_id = %s
                OR EXISTS (
                    SELECT 1 FROM shared_groups sg
                    WHERE sg.group_id = tg.id
                    AND sg.allowed_for = %s
                )
            )
        """, (new_group_id, user_id, user_id))
        if cur.fetchone() is None:
            cur.close()
            return False
        # Vérifie que la tâche appartient à un groupe accessible (propriétaire OU partagé)
        cur.execute("""
            UPDATE tasks SET group_id = %s
            WHERE id = %s
            AND group_id IN (
                SELECT tg.id FROM tasks_groups tg
                WHERE tg.owner_id = %s
                OR EXISTS (
                    SELECT 1 FROM shared_groups sg
                    WHERE sg.group_id = tg.id
                    AND sg.allowed_for = %s
                )
            )
        """, (new_group_id, task_id, user_id, user_id))
        updated = cur.rowcount > 0
        conn.commit()
        cur.close()
        return updated
    finally:
        release_db(conn)


def db_get_groups(owner_id: int) -> list[dict]:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT tg.id, tg.name,
                   u.id        AS shared_user_id,
                   u.username  AS shared_username
            FROM tasks_groups tg
            LEFT JOIN shared_groups sg ON sg.group_id = tg.id
            LEFT JOIN users u          ON u.id = sg.allowed_for
            WHERE tg.owner_id = %s
            ORDER BY tg.name
        """, (owner_id,))
        rows = cur.fetchall()
        cur.close()

        groups: dict = {}
        for row in rows:
            gid = row[0]
            if gid not in groups:
                groups[gid] = {'id': gid, 'name': row[1], 'shared_users': []}
            if row[2]:
                groups[gid]['shared_users'].append({'id': row[2], 'username': row[3]})

        return list(groups.values())
    finally:
        release_db(conn)


def db_share_group(group_id: int, target_user_id: int, owner_id: int) -> bool:
    """Partage un groupe avec un utilisateur. Vérifie que owner_id est bien le propriétaire."""
    conn = get_db()
    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT id, name FROM tasks_groups WHERE id = %s AND owner_id = %s",
            (group_id, owner_id)
        )
        result = cur.fetchone()
        if result is None:
            cur.close()
            return False

        # Empêche le partage du groupe "Personnel"
        group_name = result[1]
        if group_name == 'Personnel':
            cur.close()
            return False

        cur.execute("""
            INSERT INTO shared_groups (group_id, allowed_for, allowed_by)
            VALUES (%s, %s, %s)
            ON CONFLICT (group_id, allowed_for) DO NOTHING
        """, (group_id, target_user_id, owner_id))

        conn.commit()
        cur.close()

        # Vérifie que la ligne est bien en base (diagnostic)
        cur2 = conn.cursor()
        cur2.execute(
            "SELECT 1 FROM shared_groups WHERE group_id=%s AND allowed_for=%s",
            (group_id, target_user_id)
        )
        found = cur2.fetchone() is not None
        cur2.close()
        print(f"[db_share_group] group={group_id} target={target_user_id} → in DB: {found}")
        return True
    finally:
        release_db(conn)


def db_revoke_share(group_id: int, target_user_id: int, owner_id: int) -> bool:
    """Révoque l'accès d'un utilisateur à un groupe."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM tasks_groups WHERE id = %s AND owner_id = %s",
            (group_id, owner_id)
        )
        if cur.fetchone() is None:
            cur.close()
            return False
        cur.execute(
            "DELETE FROM shared_groups WHERE group_id = %s AND allowed_for = %s",
            (group_id, target_user_id)
        )
        conn.commit()
        cur.close()
        return True
    finally:
        release_db(conn)


def db_delete_group(group_id: int, owner_id: int) -> bool:
    """Supprime un groupe et ses tâches."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name FROM tasks_groups WHERE id = %s AND owner_id = %s",
            (group_id, owner_id)
        )
        result = cur.fetchone()
        if result is None:
            cur.close()
            return False

        # Empêche la suppression du groupe "Personnel"
        group_name = result[1]
        if group_name == 'Personnel':
            cur.close()
            return False

        cur.execute("DELETE FROM tasks WHERE group_id = %s", (group_id,))
        cur.execute(
            "DELETE FROM tasks_groups WHERE id = %s AND owner_id = %s",
            (group_id, owner_id)
        )
        conn.commit()
        cur.close()
        return True
    finally:
        release_db(conn)

        
def db_get_all_accessible_groups(user_id: int) -> list[dict]:
    """Retourne les groupes propres + groupes partagés accessibles par l'utilisateur."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT tg.id, tg.name, FALSE AS is_received_share,
                   u.id        AS shared_user_id,
                   u.username  AS shared_username
            FROM tasks_groups tg
            LEFT JOIN shared_groups sg ON sg.group_id = tg.id
            LEFT JOIN users u          ON u.id = sg.allowed_for
            WHERE tg.owner_id = %s
            UNION
            SELECT tg.id, tg.name, TRUE AS is_received_share,
                   NULL         AS shared_user_id,
                   NULL         AS shared_username
            FROM tasks_groups tg
            JOIN shared_groups sg ON sg.group_id = tg.id
            WHERE sg.allowed_for = %s
            ORDER BY name
        """, (user_id, user_id))
        rows = cur.fetchall()
        cur.close()

        groups: dict = {}
        for row in rows:
            gid = row[0]
            if gid not in groups:
                groups[gid] = {'id': gid, 'name': row[1], 'is_received_share': bool(row[2]), 'shared_users': []}
            if row[3]:
                groups[gid]['shared_users'].append({'id': row[3], 'username': row[4]})

        return list(groups.values())
    finally:
        release_db(conn)


def db_suppr_shared(group_id: int, user_id: int) -> bool:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM shared_groups
            WHERE group_id = %s AND allowed_for = %s
        """, (group_id, user_id))
        deleted = cur.rowcount != 0
        conn.commit()   # ← c'était ça qui manquait
        cur.close()
        return deleted
    finally:
        release_db(conn)

