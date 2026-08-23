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


def _get_victoire_score_max(cur, jeu_id: int) -> bool:
    """Renvoie le sens de victoire d'un jeu (True = plus haut score gagne)."""
    cur.execute("SELECT victoire_score_max FROM jeux WHERE id = %s", (jeu_id,))
    row = cur.fetchone()
    return bool(row[0]) if row else False


def _grouper_parties(rows, victoire_score_max: bool) -> list[dict]:
    """
    Regroupe des lignes (partie_id, joueur_id, prenom, nom, score) par
    partie. Dans chaque partie, les scores sont triés (meilleur en premier)
    et le(s) gagnant(s) (en cas d'égalité) sont marqués via "gagnant": True.
    Les parties sont renvoyées de la plus récente à la plus ancienne.
    """
    parties: dict[int, list[dict]] = {}
    for partie_id, joueur_id, prenom, nom, score in rows:
        parties.setdefault(partie_id, []).append({
            "joueur_id": joueur_id, "prenom": prenom, "nom": nom, "score": score,
        })

    result = []
    for partie_id, scores in parties.items():
        best = max(s["score"] for s in scores) if victoire_score_max else min(s["score"] for s in scores)
        scores.sort(key=lambda s: s["score"], reverse=victoire_score_max)
        for s in scores:
            s["gagnant"] = (s["score"] == best)
        result.append({"partie_id": partie_id, "scores": scores})

    result.sort(key=lambda p: p["partie_id"], reverse=True)
    return result


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
    ayant joué au moins une partie complète de ce jeu), avec le score
    moyen ainsi que le score min/max personnel de chaque joueur dans ce jeu.
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
                ROUND(AVG(r.score)::numeric, 1) AS score_moyen,
                MIN(r.score) AS score_min,
                MAX(r.score) AS score_max
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
                "score_min": r[7], "score_max": r[8],
            }
            for r in rows
        ]
    finally:
        release_db(conn)


def get_extremes_jeu(jeu_id: int) -> dict:
    """
    Score le plus bas et le plus haut jamais enregistrés pour ce jeu
    (toutes parties complètes, tous joueurs confondus), avec le joueur
    et la partie concernés.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(_PARTIES_COMPLETES_CTE + """
            SELECT jp.score, j.prenom, j.nom, pc.partie_id
            FROM parties_completes pc
            JOIN joueurs_partie jp ON jp.partie_id = pc.partie_id
            JOIN joueurs j ON j.id = jp.joueur_id
            WHERE pc.jeu_id = %s
            ORDER BY jp.score ASC
            LIMIT 1
        """, (jeu_id,))
        row_min = cur.fetchone()

        cur.execute(_PARTIES_COMPLETES_CTE + """
            SELECT jp.score, j.prenom, j.nom, pc.partie_id
            FROM parties_completes pc
            JOIN joueurs_partie jp ON jp.partie_id = pc.partie_id
            JOIN joueurs j ON j.id = jp.joueur_id
            WHERE pc.jeu_id = %s
            ORDER BY jp.score DESC
            LIMIT 1
        """, (jeu_id,))
        row_max = cur.fetchone()
    finally:
        release_db(conn)

    def _fmt(row):
        if not row:
            return None
        return {"score": row[0], "prenom": row[1], "nom": row[2], "partie_id": row[3]}

    return {"score_plus_bas": _fmt(row_min), "score_plus_haut": _fmt(row_max)}


def get_parties_detail_par_jeu(jeu_id: int) -> list[dict]:
    """
    Historique complet des parties complètes d'un jeu : pour chaque
    partie, le score de chaque joueur, triés (meilleur en premier).
    Ex : [{"partie_id": 12, "scores": [{"joueur_id":1,"prenom":"Alice",
           "nom":"Dupont","score":21,"gagnant":True}, ...]}, ...]
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        victoire_score_max = _get_victoire_score_max(cur, jeu_id)

        cur.execute(_PARTIES_COMPLETES_CTE + """
            SELECT pc.partie_id, j.id, j.prenom, j.nom, jp.score
            FROM parties_completes pc
            JOIN joueurs_partie jp ON jp.partie_id = pc.partie_id
            JOIN joueurs j ON j.id = jp.joueur_id
            WHERE pc.jeu_id = %s
        """, (jeu_id,))
        rows = cur.fetchall()
    finally:
        release_db(conn)

    return _grouper_parties(rows, victoire_score_max)


def get_parties_detail_joueur_jeu(joueur_id: int, jeu_id: int) -> list[dict]:
    """
    Historique des parties d'un jeu auxquelles un joueur donné a
    participé, avec le score de TOUS les joueurs de chacune de ces
    parties (même format que get_parties_detail_par_jeu).
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        victoire_score_max = _get_victoire_score_max(cur, jeu_id)

        cur.execute(_PARTIES_COMPLETES_CTE + """
            , mes_parties AS (
                SELECT DISTINCT pc.partie_id
                FROM parties_completes pc
                JOIN joueurs_partie jp ON jp.partie_id = pc.partie_id
                WHERE pc.jeu_id = %s AND jp.joueur_id = %s
            )
            SELECT mp.partie_id, j.id, j.prenom, j.nom, jp2.score
            FROM mes_parties mp
            JOIN joueurs_partie jp2 ON jp2.partie_id = mp.partie_id
            JOIN joueurs j ON j.id = jp2.joueur_id
        """, (jeu_id, joueur_id))
        rows = cur.fetchall()
    finally:
        release_db(conn)

    return _grouper_parties(rows, victoire_score_max)


def get_stats_joueur(joueur_id: int) -> dict | None:
    """
    Statistiques détaillées d'un joueur, jeu par jeu (avec score
    moyen et score min/max personnel), avec les totaux.
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
                ROUND(AVG(r.score)::numeric, 1) AS score_moyen,
                MIN(r.score) AS score_min,
                MAX(r.score) AS score_max
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
                "score_min": r[6], "score_max": r[7],
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