from flask import Flask

from db import init_pool


def init_extensions(app: Flask) -> None:
    """Initialise les extensions partagées de l'application."""
    init_pool()
