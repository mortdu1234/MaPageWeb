"""
db/database.py
Toutes les requêtes SQL liées avec la page "Database".
"""

from . import get_db, release_db
import time

def execute_query(sql: str, timeout_ms: int = 5000, max_rows: int = 500) -> tuple[dict, None] | tuple[None, str]:
    """
    Exécute une requête SQL arbitraire et retourne le résultat.
    ⚠️ Fonction sensible : à protéger par une permission stricte, réservée aux admins.
    """
    sql = sql.strip()
    if not sql:
        return None, "Requête vide."

    # Interdit l'empilement de plusieurs instructions (ex: "DROP TABLE x; SELECT 1")
    body = sql[:-1] if sql.endswith(';') else sql
    if ';' in body:
        return None, "Une seule instruction SQL à la fois est autorisée."

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(f"SET LOCAL statement_timeout = {int(timeout_ms)}")
        start = time.monotonic()
        cur.execute(sql)
        elapsed_ms = round((time.monotonic() - start) * 1000, 1)

        if cur.description:  # requête de type SELECT
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchmany(max_rows)
            data = [{col: row[i] for i, col in enumerate(columns)} for row in rows]
            conn.commit()
            return {
                "columns": columns,
                "rows": data,
                "row_count": len(data),
                "truncated": len(data) == max_rows,
                "elapsed_ms": elapsed_ms,
                "type": "select",
            }, None
        else:  # INSERT / UPDATE / DELETE / DDL...
            affected = cur.rowcount
            conn.commit()
            return {
                "columns": [],
                "rows": [],
                "row_count": affected,
                "truncated": False,
                "elapsed_ms": elapsed_ms,
                "type": "write",
            }, None

    except Exception as exc:
        conn.rollback()
        return None, str(exc)
    finally:
        release_db(conn)

# ─── Lecture ──────────────────────────────────────────────────────────────────

def get_all_tables() -> list[str]:
    """Retourne la liste des tables publiques de la base PostgreSQL."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        rows = cur.fetchall()
        return [row[0] for row in rows]
    finally:
        release_db(conn)

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