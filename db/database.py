"""
db/database.py
Toutes les requêtes SQL liées avec la page "Database".
"""

from db import get_db, joueurs, permissions, release_db


# ─── Lecture ──────────────────────────────────────────────────────────────────

def get_all_tables() -> list[str]:
    """Retourne la liste des tables publiques de la base PostgreSQL."""
    return [
        "jeux",
        "joueurs",
        "joueurs_partie",
        "parties",
        "permissions",
        "task_shares",
        "tasks",
        "user_permissions",
        "users"
    ]

def get_all_from_table(table: str) -> tuple[dict, None] | tuple[None, str]:
    """
    Retourne toutes les lignes d'une table donnée.
    Valide que la table existe réellement en BDD avant d'exécuter la requête.
    Retourne (data_dict, None) ou (None, message_erreur).
    """
    allowed = get_all_tables()
    if table not in allowed:
        return None, f"Table « {table} » introuvable ou non autorisée."

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM "{table}" LIMIT 500')
        rows    = cur.fetchall()
        columns = [desc[0] for desc in cur.description] if cur.description else []
        data    = [
            {col: row[i] for i, col in enumerate(columns)}
            for row in rows
        ]
        return {"columns": columns, "rows": data}, None
    finally:
        release_db(conn)