"""
db/backend/stats.py
Requêtes SQL de calcul des statistiques (joueurs / jeux) à partir des
tables `parties`, `joueurs_partie`, `joueurs` et `jeux`.

Le sens de la victoire dépend du jeu : la colonne `jeux.victoire_score_max`
(BOOLEAN) indique si c'est le score le plus HAUT (TRUE) ou le plus BAS
(FALSE, valeur par défaut - ex. Skyjo) qui gagne une partie. Voir la
migration `migration_victoire_score_max.sql`.

Seules les parties "complètes" (autant de scores enregistrés dans
joueurs_partie que de nb_joueurs prévus) sont prises en compte, pour ne
pas fausser les stats avec des parties en cours de saisie.
"""

from . import get_db, release_db


# CTE réutilisée : ne garde que les parties dont tous les scores ont été saisis.
_PARTIES_COMPLETES_CTE = """
    WITH parties_completes AS (
        SELECT p.id AS partie_id, p.jeu_id
        FROM parties p
        JOIN joueurs_partie jp ON jp.partie_id = p.id
        GROUP BY p.id, p.jeu_id, p.nb_joueurs
        HAVING COUNT(jp.joueur_id) = p.nb_joueurs
    )
"""


# ─── Lecture ──────────────────────────────────────────────────────────────────

def get_all_jeux() -> list[dict]:
    """
    Retourne tous les jeux triés par nom.
    Ex : [{"id": 1, "name": "skyjo", "victoire_score_max": False}, ...]
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, victoire_score_max FROM jeux ORDER BY name ASC")
        rows = cur.fetchall()
        return [{"id": r[0], "name": r[1], "victoire_score_max": r[2]} for r in rows]
    finally:
        release_db(conn)


def get_nb_parties_par_jeu() -> list[dict]:
    """
    Nombre de parties complètes jouées, par jeu.
    Ex : [{"id": 1, "name": "skyjo", "nb_parties": 12}, ...]
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(_PARTIES_COMPLETES_CTE + """
            SELECT j.id, j.name, COUNT(pc.partie_id) AS nb_parties
            FROM jeux j
            LEFT JOIN parties_completes pc ON pc.jeu_id = j.id
            GROUP BY j.id, j.name
            ORDER BY j.name ASC
        """)
        rows = cur.fetchall()
        return [{"id": r[0], "name": r[1], "nb_parties": r[2]} for r in rows]
    finally:
        release_db(conn)


def get_classement_global() -> list[dict]:
    """
    Classement de tous les joueurs, toutes parties et tous jeux confondus.
    Ex : [{"id":1,"prenom":"Alice","nom":"Dupont","nb_parties":10,
           "nb_premiere":4,"nb_derniere":1}, ...]
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(_PARTIES_COMPLETES_CTE + """
            , scores_completes AS (
                SELECT jp.joueur_id, jp.partie_id, jp.score, pc.jeu_id
                FROM joueurs_partie jp
                JOIN parties_completes pc ON pc.partie_id = jp.partie_id
            ),
            ranked AS (
                SELECT sc.*,
                    jx.victoire_score_max,
                    MIN(sc.score) OVER (PARTITION BY sc.partie_id) AS min_score,
                    MAX(sc.score) OVER (PARTITION BY sc.partie_id) AS max_score
                FROM scores_completes sc
                JOIN jeux jx ON jx.id = sc.jeu_id
            )
            SELECT j.id, j.prenom, j.nom,
                COUNT(r.partie_id) AS nb_parties,
                COALESCE(SUM(CASE
                    WHEN r.victoire_score_max AND r.score = r.max_score THEN 1
                    WHEN NOT r.victoire_score_max AND r.score = r.min_score THEN 1
                    ELSE 0 END), 0) AS nb_premiere,
                COALESCE(SUM(CASE
                    WHEN r.victoire_score_max AND r.score = r.min_score THEN 1
                    WHEN NOT r.victoire_score_max AND r.score = r.max_score THEN 1
                    ELSE 0 END), 0) AS nb_derniere
            FROM joueurs j
            LEFT JOIN ranked r ON r.joueur_id = j.id
            GROUP BY j.id, j.prenom, j.nom
            ORDER BY nb_premiere DESC, nb_parties DESC, j.nom ASC
        """)
        rows = cur.fetchall()
        return [
            {
                "id": r[0], "prenom": r[1], "nom": r[2],
                "nb_parties": r[3], "nb_premiere": r[4], "nb_derniere": r[5],
            }
            for r in rows
        ]
    finally:
        release_db(conn)


def get_classement_par_jeu(jeu_id: int) -> list[dict]:
    """
    Classement des joueurs pour un jeu donné (uniquement les joueurs
    ayant joué au moins une partie complète de ce jeu).
    Ex : [{"id":1,"prenom":"Alice","nom":"Dupont","nb_parties":5,
           "nb_premiere":2,"nb_derniere":1,"score_moyen":34.2}, ...]
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(_PARTIES_COMPLETES_CTE + """
            , scores_completes AS (
                SELECT jp.joueur_id, jp.partie_id, jp.score, pc.jeu_id
                FROM joueurs_partie jp
                JOIN parties_completes pc ON pc.partie_id = jp.partie_id
                WHERE pc.jeu_id = %s
            ),
            ranked AS (
                SELECT sc.*,
                    jx.victoire_score_max,
                    MIN(sc.score) OVER (PARTITION BY sc.partie_id) AS min_score,
                    MAX(sc.score) OVER (PARTITION BY sc.partie_id) AS max_score
                FROM scores_completes sc
                JOIN jeux jx ON jx.id = sc.jeu_id
            )
            SELECT j.id, j.prenom, j.nom,
                COUNT(r.partie_id) AS nb_parties,
                COALESCE(SUM(CASE
                    WHEN r.victoire_score_max AND r.score = r.max_score THEN 1
                    WHEN NOT r.victoire_score_max AND r.score = r.min_score THEN 1
                    ELSE 0 END), 0) AS nb_premiere,
                COALESCE(SUM(CASE
                    WHEN r.victoire_score_max AND r.score = r.min_score THEN 1
                    WHEN NOT r.victoire_score_max AND r.score = r.max_score THEN 1
                    ELSE 0 END), 0) AS nb_derniere,
                ROUND(AVG(r.score)::numeric, 1) AS score_moyen
            FROM joueurs j
            JOIN ranked r ON r.joueur_id = j.id
            GROUP BY j.id, j.prenom, j.nom
            ORDER BY nb_premiere DESC, score_moyen ASC
        """, (jeu_id,))
        rows = cur.fetchall()
        return [
            {
                "id": r[0], "prenom": r[1], "nom": r[2],
                "nb_parties": r[3], "nb_premiere": r[4], "nb_derniere": r[5],
                "score_moyen": float(r[6]) if r[6] is not None else None,
            }
            for r in rows
        ]
    finally:
        release_db(conn)


def get_stats_joueur(joueur_id: int) -> dict | None:
    """
    Statistiques détaillées d'un joueur, jeu par jeu, avec les totaux.
    Retourne None si le joueur n'existe pas.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, prenom, nom FROM joueurs WHERE id = %s",
            (joueur_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        joueur = {"id": row[0], "prenom": row[1], "nom": row[2]}

        cur.execute(_PARTIES_COMPLETES_CTE + """
            , scores_completes AS (
                SELECT jp.joueur_id, jp.partie_id, jp.score, pc.jeu_id
                FROM joueurs_partie jp
                JOIN parties_completes pc ON pc.partie_id = jp.partie_id
            ),
            ranked AS (
                SELECT sc.*,
                    jx2.victoire_score_max,
                    MIN(sc.score) OVER (PARTITION BY sc.partie_id) AS min_score,
                    MAX(sc.score) OVER (PARTITION BY sc.partie_id) AS max_score
                FROM scores_completes sc
                JOIN jeux jx2 ON jx2.id = sc.jeu_id
            )
            SELECT jx.id, jx.name,
                COUNT(r.partie_id) AS nb_parties,
                COALESCE(SUM(CASE
                    WHEN r.victoire_score_max AND r.score = r.max_score THEN 1
                    WHEN NOT r.victoire_score_max AND r.score = r.min_score THEN 1
                    ELSE 0 END), 0) AS nb_premiere,
                COALESCE(SUM(CASE
                    WHEN r.victoire_score_max AND r.score = r.min_score THEN 1
                    WHEN NOT r.victoire_score_max AND r.score = r.max_score THEN 1
                    ELSE 0 END), 0) AS nb_derniere,
                ROUND(AVG(r.score)::numeric, 1) AS score_moyen
            FROM jeux jx
            JOIN ranked r ON r.jeu_id = jx.id AND r.joueur_id = %s
            GROUP BY jx.id, jx.name
            ORDER BY jx.name ASC
        """, (joueur_id,))
        rows = cur.fetchall()
        par_jeu = [
            {
                "jeu_id": r[0], "jeu": r[1], "nb_parties": r[2],
                "nb_premiere": r[3], "nb_derniere": r[4],
                "score_moyen": float(r[5]) if r[5] is not None else None,
            }
            for r in rows
        ]

        joueur["par_jeu"] = par_jeu
        joueur["nb_parties_total"] = sum(p["nb_parties"] for p in par_jeu)
        joueur["nb_premiere_total"] = sum(p["nb_premiere"] for p in par_jeu)
        joueur["nb_derniere_total"] = sum(p["nb_derniere"] for p in par_jeu)
        return joueur
    finally:
        release_db(conn)