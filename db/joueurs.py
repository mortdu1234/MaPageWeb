"""
db/joueurs.py
Toutes les requêtes SQL liées à la table `joueurs`.
"""

from db import get_db, release_db


# ─── Lecture ──────────────────────────────────────────────────────────────────

def get_all_joueurs() -> list[dict]:
    """
    Retourne tous les joueurs triés par nom puis prénom.
    Ex : [{"id": 1, "prenom": "Alice", "nom": "Dupont"}, ...]
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, prenom, nom
            FROM joueurs
            ORDER BY nom ASC, prenom ASC
        """)
        rows = cur.fetchall()
        return [{"id": r[0], "prenom": r[1], "nom": r[2]} for r in rows]
    finally:
        release_db(conn)


def get_joueur_by_id(joueur_id: int) -> dict | None:
    """
    Retourne un joueur par son id, ou None si introuvable.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, prenom, nom FROM joueurs WHERE id = %s",
            (joueur_id,)
        )
        row = cur.fetchone()
        return {"id": row[0], "prenom": row[1], "nom": row[2]} if row else None
    finally:
        release_db(conn)


def joueur_exists(prenom: str, nom: str) -> bool:
    """Retourne True si un joueur avec ce prénom et ce nom existe déjà."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM joueurs WHERE prenom = %s AND nom = %s",
            (prenom, nom)
        )
        return cur.fetchone() is not None
    finally:
        release_db(conn)


# ─── Écriture ─────────────────────────────────────────────────────────────────

def create_joueur(prenom: str, nom: str) -> int:
    """
    Crée un joueur. Retourne l'id du nouveau joueur.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO joueurs (prenom, nom) VALUES (%s, %s) RETURNING id",
            (prenom, nom)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return new_id
    finally:
        release_db(conn)


def delete_joueur(joueur_id: int) -> bool:
    """
    Supprime un joueur par son id. Retourne True si supprimé, False si introuvable.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM joueurs WHERE id = %s", (joueur_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    finally:
        release_db(conn)