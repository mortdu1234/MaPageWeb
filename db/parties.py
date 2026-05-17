"""
db/parties.py
Toutes les requêtes SQL pour créer et consulter des parties de jeu.
"""

from db import get_db, release_db

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
        id_partie = cur.fetchone()[0]

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