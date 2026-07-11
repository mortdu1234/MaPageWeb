"""
app/core/blueprint_utils.py

Chaque module (core/* et features/*) a son propre dossier static/
et templates/. Un Blueprint Flask classique donne par défaut le même
static_url_path ("/static") à tout le monde -> collision garantie dès
qu'on a 2 modules avec un static_folder.

Ce helper force un static_url_path unique basé sur le nom du blueprint,
donc AUCUN routes.py n'a besoin de s'en soucier : il suffit d'appeler
make_blueprint(...) au lieu de Blueprint(...) directement.
"""

from flask import Blueprint


def make_blueprint(name: str, import_name: str, url_prefix: str | None = None) -> Blueprint:
    """
    name        : nom unique du blueprint, ex "qwirkle", "base", "servers_hub"
    import_name : toujours __name__ (appelant)
    url_prefix  : préfixe des routes, ex "/jeux/qwirkle". None = pas de préfixe (racine).
    """
    return Blueprint(
        name,
        import_name,
        template_folder="templates",
        static_folder="static",
        static_url_path=f"/static/{name}",  # unique -> jamais de collision
        url_prefix=url_prefix,
    )