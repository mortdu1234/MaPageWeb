import logging

from flask import Blueprint, jsonify

from config import Config

rsaKeys_bp = Blueprint("rsaKeys", __name__)

logger = logging.getLogger(__name__)


@rsaKeys_bp.route("/get_rsa_public_key", methods=["GET"])
def get_rsa_public_key():
    try:
        with open(Config.RSA_PUBLIC_KEY_PATH, "r", encoding="utf-8") as f:
            public_key = f.read()
    except FileNotFoundError:
        logger.error("Clé publique RSA introuvable : %s", Config.RSA_PUBLIC_KEY_PATH)
        return jsonify({"error": "Clé publique indisponible"}), 503
    except OSError as exc:
        logger.exception("Erreur de lecture de la clé publique RSA")
        return jsonify({"error": "Erreur serveur"}), 500

    return jsonify({"public_key": public_key})