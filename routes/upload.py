import base64
import json
import logging
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from flask import Blueprint, current_app, jsonify, render_template, request
from werkzeug.utils import secure_filename

upload_bp = Blueprint("upload", __name__)

ALLOWED_EXTENSION   = "enc"
MAX_FILE_SIZE_BYTES = 16 * 1024 * 1024  # 16 Mo

logger = logging.getLogger(__name__)


# ── Helpers génériques ────────────────────────────────────────────────────────

def _allowed_file(filename: str) -> bool:
    return filename.rsplit(".", 1)[-1].lower() == ALLOWED_EXTENSION if "." in filename else False


def _unique_path(folder: str, filename: str) -> str:
    """Retourne un chemin libre en ajoutant un compteur si le fichier existe déjà."""
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(folder, filename)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(folder, f"{base}_{counter}{ext}")
        counter += 1
    return candidate


# ── Chargement de la clé privée RSA ──────────────────────────────────────────

def _load_rsa_private_key(path: str, passphrase: bytes | None = None):
    """
    Charge la clé privée RSA depuis un fichier PEM.
    `passphrase` doit être fourni (en bytes) si la clé est chiffrée.
    """
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=passphrase)


# ── Déchiffrement hybride RSA-OAEP + AES-256-GCM ─────────────────────────────

def _decrypt_file(
    ciphertext: bytes,
    wrapped_key_b64: str,
    iv_b64: str,
    private_key,
) -> bytes:
    """
    Déchiffre un fichier chiffré côté client avec le schéma hybride :
      - RSA-OAEP / SHA-256  →  unwrap de la clé AES-256
      - AES-256-GCM         →  déchiffrement du contenu

    WebCrypto annexe le tag GCM (16 octets) à la fin du chiffré ;
    AESGCM de cryptography le gère nativement.

    Lève ValueError si l'une des deux étapes échoue.
    """
    # 1. Décoder les champs Base64
    try:
        wrapped_key = base64.b64decode(wrapped_key_b64)
        iv          = base64.b64decode(iv_b64)
    except Exception as exc:
        raise ValueError(f"Métadonnées Base64 invalides : {exc}") from exc

    # 2. Unwrap de la clé AES avec RSA-OAEP
    try:
        aes_key_bytes = private_key.decrypt(
            wrapped_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except Exception as exc:
        raise ValueError(f"Échec RSA-OAEP (clé privée invalide ?) : {exc}") from exc

    # 3. Déchiffrement AES-256-GCM
    try:
        plaintext = AESGCM(aes_key_bytes).decrypt(iv, ciphertext, None)
    except Exception as exc:
        raise ValueError(f"Échec AES-GCM (données corrompues ou tag invalide) : {exc}") from exc

    return plaintext


# ── Routes ────────────────────────────────────────────────────────────────────

@upload_bp.route("/upload", methods=["GET"])
def upload_page():
    return render_template("upload.html")


@upload_bp.route("/upload", methods=["POST"])
def upload_file():
    # ── Validation de base ───────────────────────────────────────────────────
    files = request.files.getlist("files")
    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "Aucun fichier reçu"}), 400

    raw_meta = request.form.get("encryption_meta")
    if not raw_meta:
        return jsonify({"error": "Métadonnées de chiffrement manquantes"}), 400

    try:
        enc_meta: list[dict] = json.loads(raw_meta)
    except json.JSONDecodeError:
        return jsonify({"error": "Métadonnées de chiffrement invalides"}), 400

    meta_by_index: dict[int, dict] = {item["index"]: item for item in enc_meta}

    # ── Chargement de la clé privée ──────────────────────────────────────────
    private_key_path = current_app.config.get("RSA_PRIVATE_KEY_PATH")
    private_key_pass = current_app.config.get("RSA_PRIVATE_KEY_PASSPHRASE")  # bytes | None

    if not private_key_path:
        logger.error("RSA_PRIVATE_KEY_PATH non configuré dans l'application Flask")
        return jsonify({"error": "Configuration serveur incomplète"}), 500

    try:
        private_key = _load_rsa_private_key(private_key_path, private_key_pass)
    except FileNotFoundError:
        logger.error("Clé privée RSA introuvable : %s", private_key_path)
        return jsonify({"error": "Clé privée indisponible"}), 503
    except Exception:
        logger.exception("Impossible de charger la clé privée RSA")
        return jsonify({"error": "Erreur serveur"}), 500

    upload_folder: str = current_app.config.get("UPLOAD_FOLDER", "uploads")
    os.makedirs(upload_folder, exist_ok=True)

    results = []

    for i, file in enumerate(files):
        name = file.filename or ""
        if not name:
            continue

        # ── Validation du type ───────────────────────────────────────────────
        if not _allowed_file(name):
            results.append({"name": name, "status": "error", "message": "Type non autorisé"})
            continue

        # ── Validation de la taille ──────────────────────────────────────────
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)

        if size > MAX_FILE_SIZE_BYTES:
            results.append({"name": name, "status": "error", "message": "Fichier trop volumineux (16 Mo max)"})
            continue

        # ── Vérification des métadonnées ─────────────────────────────────────
        meta = meta_by_index.get(i)
        if not meta or not meta.get("wrapped_key") or not meta.get("iv"):
            results.append({"name": name, "status": "error", "message": "Métadonnées de chiffrement manquantes"})
            continue

        # ── Déchiffrement ────────────────────────────────────────────────────
        ciphertext = file.read()

        try:
            plaintext = _decrypt_file(
                ciphertext,
                wrapped_key_b64=meta["wrapped_key"],
                iv_b64=meta["iv"],
                private_key=private_key,
            )
        except ValueError as exc:
            logger.warning("Déchiffrement échoué pour %s : %s", name, exc)
            results.append({"name": name, "status": "error", "message": str(exc)})
            continue

        # ── Sauvegarde du fichier en clair ────────────────────────────────────
        # On restaure le nom d'origine (sans le suffixe .enc ajouté côté client)
        original_name = meta.get("original_name") or name.removesuffix(".enc")
        safe_name     = secure_filename(original_name)
        save_path     = _unique_path(upload_folder, safe_name)

        try:
            with open(save_path, "wb") as out:
                out.write(plaintext)
        except OSError:
            logger.exception("Impossible d'écrire %s", safe_name)
            results.append({"name": safe_name, "status": "error", "message": "Erreur d'écriture sur le serveur"})
            continue

        size_kb = round(len(plaintext) / 1024, 1)
        logger.info("Fichier déchiffré et sauvegardé : %s (%s Ko)", safe_name, size_kb)
        results.append({"name": os.path.basename(save_path), "status": "ok", "size_kb": size_kb})

    return jsonify({"files": results})


# ── Enregistrement dans l'application principale ─────────────────────────────
#
# from upload import upload_bp
#
# app = Flask(__name__)
# app.config["UPLOAD_FOLDER"]              = "uploads"
# app.config["MAX_CONTENT_LENGTH"]         = 16 * 1024 * 1024
# app.config["RSA_PRIVATE_KEY_PATH"]       = "keys/private.pem"
# app.config["RSA_PRIVATE_KEY_PASSPHRASE"] = None  # ou b"mon_mot_de_passe"
#
# app.register_blueprint(upload_bp)