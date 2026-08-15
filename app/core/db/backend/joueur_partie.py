"""
db/joueur_partie.py
Toutes les requêtes SQL liées à la table `joueurs_partie`.
"""

from . import get_db, release_db


# ─── Lecture ──────────────────────────────────────────────────────────────────


# ─── Écriture ─────────────────────────────────────────────────────────────────

def insert_joueur_partie(joueur_id: int, partie_id: int, score: int) -> None:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO joueurs_partie (joueur_id, partie_id, score) VALUES (%s, %s, %s)",
            (joueur_id, partie_id, score)
        )
        conn.commit()
    finally:
        release_db(conn)