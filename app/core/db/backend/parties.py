"""
db/parties.py
Toutes les requêtes SQL pour créer et consulter des parties de jeu.
"""

from . import get_db, release_db

# --------- CONSULTATIONS DE PARTIES ---------
def get_jeu_id_by_jeu_name(jeu: str) -> int | None:
    """
    Retourne l'ID d'un jeu donné par son nom.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM jeux WHERE name = %s",
            (jeu,)
        )
        rows = cur.fetchall()
        return rows[0][0] if rows else None
    finally:
        release_db(conn)


def get_parties_by_jeu(jeu: str) -> list[dict]:
    """
    Retourne les parties INCOMPLÈTES d'un jeu donné, les plus récentes en
    premier (par id décroissant). Une partie est "incomplète" tant que le
    nombre de scores déjà enregistrés (table joueurs_partie) est inférieur
    à son nb_joueurs.
    Ex : [{"id": 12, "nb_joueurs": 4, "nb_scores": 2}, ...]
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.nb_joueurs, COUNT(jp.joueur_id) AS nb_scores
            FROM parties p
            JOIN jeux j ON j.id = p.jeu_id
            LEFT JOIN joueurs_partie jp ON jp.partie_id = p.id
            WHERE j.name = %s
            GROUP BY p.id, p.nb_joueurs
            HAVING COUNT(jp.joueur_id) < p.nb_joueurs
            ORDER BY p.id DESC
        """, (jeu,))
        rows = cur.fetchall()
        return [{"id": r[0], "nb_joueurs": r[1], "nb_scores": r[2]} for r in rows]
    finally:
        release_db(conn)


# --------- CREATIONS DE PARTIES ---------
def create_partie(donnees: dict):
    """
    Crée une partie avec les données fournies
    """
    def validate_data_send(data: dict):
        assert isinstance(data, dict), "data doit être un dict"

        assert "jeu" in data,         "clé 'jeu' manquante"
        assert "nb_joueurs" in data,  "clé 'nb_joueurs' manquante"
        assert "scores" in data,      "clé 'scores' manquante"

        assert isinstance(data["jeu"], str),       "'jeu' doit être une str"
        assert isinstance(data["nb_joueurs"], int), "'nb_joueurs' doit être un int"
        assert isinstance(data["scores"], dict),   "'scores' doit être un dict"

        for k, v in data["scores"].items():
            assert isinstance(k, int), f"clé de scores '{k}' doit être un int"
            assert isinstance(v, int), f"valeur de scores '{v}' doit être un int"

        assert len(data["scores"]) == data["nb_joueurs"], \
            f"scores a {len(data['scores'])} entrées mais nb_joueurs vaut {data['nb_joueurs']}"

    validate_data_send(donnees)

    nom_jeu    = donnees["jeu"]
    nb_joueurs = donnees["nb_joueurs"]
    scores     = donnees["scores"]

    id_jeu = get_jeu_id_by_jeu_name(nom_jeu)
    if id_jeu is None:
        raise ValueError(f"Jeu introuvable en base : {nom_jeu!r}")

    conn = get_db()
    try:
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO parties (jeu_id, nb_joueurs) VALUES (%s, %s) RETURNING id;",
            (id_jeu, nb_joueurs)
        )
        id_partie = cur.fetchone()[0] # type: ignore

        for id_joueur, score in scores.items():
            cur.execute(
                "INSERT INTO joueurs_partie (joueur_id, partie_id, score) VALUES (%s, %s, %s);",
                (id_joueur, id_partie, score)
            )

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        release_db(conn)


def create_partie_simple(jeu: str, nb_joueurs: int) -> int:
    """
    Crée une partie "vide" pour un jeu donné (sans scores initiaux), avec
    un nombre de joueurs attendu donné. Utile pour le formulaire d'envoi
    de score joueur par joueur : on crée la partie une fois avec son
    nombre de joueurs, puis on y rattache les scores au fur et à mesure
    via submit_score() / insert_joueur_partie(). La partie disparaît de
    la liste des parties sélectionnables (get_parties_by_jeu) dès qu'elle
    a reçu autant de scores que de joueurs.

    Retourne l'id de la nouvelle partie.
    """
    id_jeu = get_jeu_id_by_jeu_name(jeu)
    if id_jeu is None:
        raise ValueError(f"Jeu introuvable en base : {jeu!r}")

    if not isinstance(nb_joueurs, int) or nb_joueurs < 1:
        raise ValueError("nb_joueurs doit être un entier positif.")

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO parties (jeu_id, nb_joueurs) VALUES (%s, %s) RETURNING id;",
            (id_jeu, nb_joueurs)
        )
        new_id = cur.fetchone()[0]  # type: ignore
        conn.commit()
        return new_id
    finally:
        release_db(conn)