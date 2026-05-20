"""
db/users.py
"""

from db import get_db, release_db
import bcrypt


def get_all_users() -> list[dict]:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, username FROM users ORDER BY username")
        rows = cur.fetchall()
        cur.close()
        return [{"id": r[0], "username": r[1]} for r in rows]
    finally:
        release_db(conn)


def get_user_by_username(username: str):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, password FROM users WHERE username = %s",
            (username,)
        )
        row = cur.fetchone()
        cur.close()
        return row
    finally:
        release_db(conn)


def get_user_by_id(user_id: int):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username FROM users WHERE id = %s",
            (user_id,)
        )
        row = cur.fetchone()
        cur.close()
        return row
    finally:
        release_db(conn)


def username_exists(username: str) -> bool:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        exists = cur.fetchone() is not None
        cur.close()
        return exists
    finally:
        release_db(conn)


def create_user(username: str, password: str) -> int:
    hashed_password = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt(rounds=12)
    ).decode('utf-8')

    conn = get_db()
    try:
        cur = conn.cursor()

        # Crée l'utilisateur
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
            (username, hashed_password)
        )
        new_id = cur.fetchone()[0]

        # Crée le groupe par défaut  ← nom de table corrigé : tasks_groups
        cur.execute("""
            INSERT INTO tasks_groups (name, owner_id)
            VALUES ('Personnel', %s)
        """, (new_id,))

        conn.commit()   # ← un seul commit pour les deux INSERT
        cur.close()
        return new_id
    finally:
        release_db(conn)


def verify_password(plain_password: str, stored_password) -> bool:
    pwd_bytes = plain_password.encode('utf-8')
    if isinstance(stored_password, str):
        hash_bytes = stored_password.encode('utf-8')
    else:
        hash_bytes = stored_password
    return bcrypt.checkpw(pwd_bytes, hash_bytes)