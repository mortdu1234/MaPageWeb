"""
db/files.py
Toutes les requêtes SQL liées aux tables `files` et `file_shares`.
"""

from db import get_db, release_db


# ─── Lecture ──────────────────────────────────────────────────────────────────

def get_files_by_user_id(user_id: int) -> list[dict]:
    """Retourne tous les fichiers appartenant à un utilisateur."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, file_name, stored_filename, uploaded_at
            FROM files
            WHERE user_id = %s
            ORDER BY uploaded_at DESC
        """, (user_id,))
        rows = cur.fetchall()
        cols = ["id", "file_name", "stored_filename", "uploaded_at"]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        release_db(conn)


def get_files_shared_with_user(user_id: int) -> list[dict]:
    """Retourne les fichiers partagés avec l'utilisateur."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT f.id, f.file_name, f.stored_filename,
                   u.username AS shared_by,
                   fs.shared_at
            FROM files f
            JOIN file_shares fs ON f.id = fs.file_id
            JOIN users u ON fs.shared_by_user_id = u.id
            WHERE fs.shared_with_user_id = %s
            ORDER BY fs.shared_at DESC
        """, (user_id,))
        rows = cur.fetchall()
        cols = ["id", "file_name", "stored_filename", "shared_by", "shared_at"]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        release_db(conn)


def get_shared_user_ids_for_file(file_id: int) -> list[int]:
    """Retourne la liste des user_id avec qui un fichier est partagé."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT shared_with_user_id FROM file_shares WHERE file_id = %s
        """, (file_id,))
        return [r[0] for r in cur.fetchall()]
    finally:
        release_db(conn)


def get_file_by_id(file_id: int) -> dict | None:
    """Retourne un fichier par son id (pour vérification d'ownership)."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, file_name, stored_filename, user_id, uploaded_at
            FROM files
            WHERE id = %s
        """, (file_id,))
        row = cur.fetchone()
        if not row:
            return None
        cols = ["id", "file_name", "stored_filename", "user_id", "uploaded_at"]
        return dict(zip(cols, row))
    finally:
        release_db(conn)


# ─── Écriture ─────────────────────────────────────────────────────────────────

def add_new_file(file_name: str, stored_filename: str, user_id: int) -> int:
    """Insère un nouveau fichier et retourne son id."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO files
              (user_id, file_name, stored_filename)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (user_id, file_name, stored_filename))
        file_id = cur.fetchone()[0]
        conn.commit()
        return file_id
    finally:
        release_db(conn)


def delete_file(file_id: int) -> None:
    """Supprime physiquement un fichier de la base."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM files WHERE id = %s", (file_id,))
        conn.commit()
    finally:
        release_db(conn)


def add_file_share(file_id: int, shared_by_user_id: int, shared_with_user_id: int):
    """Partage un fichier avec un utilisateur (insère ou ignore si déjà existant)."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO file_shares
              (file_id, shared_by_user_id, shared_with_user_id)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (file_id, shared_by_user_id, shared_with_user_id))
        conn.commit()
    finally:
        release_db(conn)


def remove_file_share(file_id: int, shared_with_user_id: int):
    """Supprime le partage d'un fichier avec un utilisateur."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM file_shares
            WHERE file_id = %s AND shared_with_user_id = %s
        """, (file_id, shared_with_user_id))
        conn.commit()
    finally:
        release_db(conn)