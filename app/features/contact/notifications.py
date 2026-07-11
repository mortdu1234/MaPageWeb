"""Service de notifications du package app."""

from app.config import Config
import requests

PRIORITES = {
    "min": 1,
    "low": 2,
    "default": 3,
    "high": 4,
    "urgent": 5,
}


def notifier(
    titre: str,
    message: str,
    priorite: str = "default",
    tags: list[str] | None = None,
    lien: str = Config.WEB_SITE_URL,
):
    headers = {
        "Title": titre,
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
    except requests.exceptions.RequestException:
        return False
