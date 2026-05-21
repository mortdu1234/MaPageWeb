"""
Gestion de l'envois et de notifiactions
"""
from config import Config
import requests

PRIORITES = {
    "min":     1,
    "low":     2,
    "default": 3,
    "high":    4,
    "urgent":  5,
}


def notifier(
    titre: str,
    message: str,
    priorite: str = "default",
    tags: list[str] | None = None,
    lien: str = Config.WEB_SITE_URL
):
    """
    Envoie une notification push via ntfy.

    Args:
        titre    : Titre affiché
        message  : Corps de la notification
        priorite : "min" | "low" | "default" | "high" | "urgent"
        tags     : Liste d'emojis/tags ex: ["warning", "rotating_light"]
        lien     : URL cliquable dans la notification (défaut: page du .env)

    Returns:
        True si succès, False sinon
    """

    headers = {
        "Title":    titre,
        "Priority": str(PRIORITES.get(priorite, 3)),
        "Content-Type": "text/plain; charset=utf-8",
    }

    if tags:
        headers["Tags"] = ",".join(tags)

    if lien:
        headers["Click"] = lien

    try:
        resp = requests.post(Config.NOTIFICATIONS_URL, data=message.encode("utf-8"), headers=headers, timeout=5)
        resp.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        return False
