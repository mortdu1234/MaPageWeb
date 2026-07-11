"""Adaptateur de compatibilité pour les données de jeux."""

from db.joueurs import *
from db.parties import *

__all__ = [
    "create_joueur",
    "get_all_joueurs",
    "create_partie",
]
