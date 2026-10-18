import json
from pathlib import Path

REQUIRED = ("nom", "date", "type", "court", "accroche", "stack")
TYPES = ("academique", "personnel")


def load_header(bp):
    """Lit static/json/header.json du dossier d'un projet.

    Ce fichier alimente à la fois l'infobox du hub et l'en-tête de la page du projet.
    Champs : nom, date, type ("academique" | "personnel"), git (URL ou null),
    court (description de l'infobox), accroche (phrase du CV), stack (liste).
    """
    path = Path(bp.root_path) / "static" / "json" / "header.json"
    with path.open(encoding="utf-8") as f:
        header = json.load(f)

    missing = [k for k in REQUIRED if k not in header]
    if missing:
        raise ValueError(f"{path} : clés manquantes {missing}")
    if header["type"] not in TYPES:
        raise ValueError(f"{path} : type doit être 'academique' ou 'personnel'")

    header.setdefault("git", None)
    header["endpoint"] = f"projets.{bp.name}.index"  # utilisé par l'infobox pour le lien
    return header
