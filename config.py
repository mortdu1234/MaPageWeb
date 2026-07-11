import os
from dotenv import load_dotenv

load_dotenv()



def _require(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise EnvironmentError(f"[CONFIG] Variable manquante ou vide : {key}")
    return value


class Config:
    SECRET_KEY  = _require("SECRET_KEY")
    DEBUG       = False
    TESTING     = False

    DB_HOST     = _require("DB_HOST")
    DB_PORT     = _require("DB_PORT")
    DB_NAME     = _require("DB_NAME")
    DB_USER     = _require("DB_USER")
    DB_PASSWORD = _require("DB_PASSWORD")

    RSA_PUBLIC_KEY_PATH  = _require("RSA_PUBLIC_KEY_PATH")
    RSA_PRIVATE_KEY_PATH = _require("RSA_PRIVATE_KEY_PATH")

    UPLOAD_FOLDER = _require("UPLOAD_FOLDER")

    NOTIFICATIONS_URL = _require("NOTIFICATIONS_URL")
    WEB_SITE_URL = _require("WEB_SITE_URL")

    PANEL_URL = _require("PANEL_URL")
    CLIENT_API_KEY = _require("CLIENT_API_KEY")

MINIGAME_VM_HOST = _require("MINIGAME_VM_HOST")
MINIGAME_VM_PORT = _require("MINIGAME_VM_PORT")
MINIGAME_VM_USER = _require("MINIGAME_VM_USER")
MINIGAME_VM_SSH_KEY_PATH = _require("MINIGAME_VM_SSH_KEY_PATH")
MINIGAME_VM_SCRIPT_PATH = _require("MINIGAME_VM_SCRIPT_PATH")
MINIGAME_VM_JSON_PATH = _require("MINIGAME_VM_JSON_PATH")

MINIGAME_VM_PTERODACTYL_ID = _require("MINIGAME_VM_PTERODACTYL_ID")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    DEBUG   = True