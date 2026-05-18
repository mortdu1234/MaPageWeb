"""
db/users.py
Toutes les requêtes SQL liées à la table `users`.
"""

from db import get_db, release_db
import bcrypt


# ─── Lecture ──────────────────────────────────────────────────────────────────

def get_all_users() -> list[dict]:
    """Retourne la liste de tous les utilisateurs (id, username)."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, username FROM users ORDER BY username")
        rows = cur.fetchall()
        return [{"id": r[0], "username": r[1]} for r in rows]
    finally:
        release_db(conn)

def get_user_by_username(username: str):
    """
    Retourne (id, username, password) ou None si introuvable.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, password FROM users WHERE username = %s",
            (username,)
        )
        return cur.fetchone()
    finally:
        release_db(conn)


def get_user_by_id(user_id: int):
    """
    Retourne (id, username) ou None.
    Utilisé pour vérifier qu'un compte existe toujours.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username FROM users WHERE id = %s",
            (user_id,)
        )
        return cur.fetchone()
    finally:
        release_db(conn)


def username_exists(username: str) -> bool:
    """Retourne True si le nom d'utilisateur est déjà pris."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        return cur.fetchone() is not None
    finally:
        release_db(conn)


# ─── Écriture ─────────────────────────────────────────────────────────────────

def create_user(username: str, password: str) -> int:
    """
    Crée un utilisateur. Retourne l'id du nouvel utilisateur.
    Le mot de passe est haché avec bcrypt et stocké sous forme de chaîne (VARCHAR).
    """
    hashed_password = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt(rounds=12)
    ).decode('utf-8')  # stocker en str pour éviter les problèmes de type avec psycopg2

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
            (username, hashed_password)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return new_id
    finally:
        release_db(conn)


# ─── Authentification ─────────────────────────────────────────────────────────

def verify_password(plain_password: str, stored_password) -> bool:
    """
    Vérifie le mot de passe saisi face au hash stocké en base.
    Accepte stored_password en str ou en bytes (selon le driver / la colonne).
    """
    pwd_bytes = plain_password.encode('utf-8')

    # Normalise le hash en bytes quel que soit ce que le driver renvoie
    if isinstance(stored_password, str):
        print("choix 1")
        hash_bytes = stored_password.encode('utf-8')
    else:
        print("choix 2")
        hash_bytes = stored_password

    return bcrypt.checkpw(pwd_bytes, hash_bytes)