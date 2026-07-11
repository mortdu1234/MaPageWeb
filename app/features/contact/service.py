"""Service de contact du package app."""

from app.features.contact.notifications import notifier


def contact_send(nom: str, email: str, message: str):
    return notifier(
        f"Mail de:{nom}",
        f"from:{email}\nmessage:\n{message}",
        "high",
        ["Contact"],
    )
