"""
app/core/blueprint_utils.py

Chaque module (core/* et features/*) a son propre dossier static/
et templates/. Un Blueprint Flask classique donne par défaut le même
static_url_path ("/static") à tout le monde -> collision garantie dès
qu'on a 2 modules avec un static_folder. Idem pour les templates :
Flask cherche dans un espace de noms plat, donc 2 fichiers "hub.html"
dans 2 modules différents entrent en collision.

Ce helper :
  - force un static_url_path unique basé sur le chemin du fichier appelant
  - enregistre un PrefixLoader Jinja dédié par blueprint, namespacé par
    bp.name, pour éviter toute collision de templates SANS avoir à
    déplacer les fichiers .html existants.
"""

import os

from flask import Blueprint as _Blueprint
from jinja2 import ChoiceLoader, FileSystemLoader, PrefixLoader

# Racine du projet = dossier PARENT de "app"
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)


class Blueprint(_Blueprint):
    def get_templates_path(self, filename: str) -> str:
        """
        Namespace virtuel (via PrefixLoader) basé sur le nom du blueprint.
        Les fichiers .html restent physiquement dans templates/ sans
        sous-dossier -> pas de déplacement nécessaire.
        """
        return f"{self.name}/{filename}"


def make_blueprint(name: str, import_name: str, caller_file: str, url_prefix: str | None = None) -> Blueprint:
    """
    name        : nom unique du blueprint, ex "qwirkle", "base", "servers_hub"
    import_name : toujours __name__ (appelant)
    caller_file : toujours __file__ (appelant)
    url_prefix  : préfixe des routes, ex "/jeux/qwirkle". None = pas de préfixe (racine).
    """
    caller_dir = os.path.dirname(os.path.abspath(caller_file))
    rel_path = os.path.relpath(caller_dir, _PROJECT_ROOT)
    url_path_part = rel_path.replace(os.sep, "/")

    static_url_path = f"/{url_path_part}/static"
    template_dir = os.path.join(caller_dir, "templates")

    # On désactive le template_folder par défaut du Blueprint : on gère
    # nous-mêmes la résolution via PrefixLoader (voir _register_loader).
    bp = Blueprint(
        name,
        import_name,
        template_folder=None,
        static_folder="static",
        static_url_path=static_url_path,
        url_prefix=url_prefix,
    )

    @bp.record_once
    def _register_loader(state):
        app = state.app
        if not isinstance(app.jinja_loader, ChoiceLoader):
            app.jinja_loader = ChoiceLoader([app.jinja_loader])
        app.jinja_loader.loaders.append(
            PrefixLoader({name: FileSystemLoader(template_dir)})
        )

    return bp