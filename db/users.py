"""
db/users.py
Toutes les requêtes SQL liées à la table `users`.
"""

from db import get_db, release_db


# ─── Lecture ──────────────────────────────────────────────────────────────────

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
    TODO: hasher le mot de passe avec bcrypt avant stockage.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
            (username, password)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return new_id
    finally:
        release_db(conn)


# ─── Authentification ─────────────────────────────────────────────────────────

def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Vérifie le mot de passe.
    TODO: remplacer par bcrypt.checkpw quand les mots de passe seront hachés.
    """
    return plain_password == stored_password