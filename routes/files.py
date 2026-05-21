"""
routes/files_routes.py
Blueprint Flask pour la gestion des fichiers.
"""

import os
from backend.FilesService import FileService
from flask import Blueprint, render_template, request, jsonify, send_file, abort
from sessionUser import SessionUser
from db.files import (
    get_files_by_user_id,
    get_files_shared_with_user,
    get_shared_user_ids_for_file,
    add_new_file,
    add_file_share,
    remove_file_share,
    get_file_by_id,
    delete_file,
)
from db.users import get_all_users
from backend.crypto import encrypt_file, decrypt_file

files_bp = Blueprint("files", __name__, url_prefix="/files")

# ── Dossier de stockage ──────────────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ─── Page principale ─────────────────────────────────────────────────────────
@files_bp.route("/")
def index():
    my_files_raw = get_files_by_user_id(SessionUser.user_id())
    shared_files = get_files_shared_with_user(SessionUser.user_id())
    all_users    = get_all_users()

    my_files = []
    for f in my_files_raw:
        f["shared_with_ids"] = get_shared_user_ids_for_file(f["id"])
        my_files.append(f)

    return render_template(
        "files.html",
        my_files=my_files,
        shared_files=shared_files,
        all_users=all_users,
    )


@files_bp.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400
    try:
        FileService.upload(request.files["file"], SessionUser.user_id())
        return jsonify({"message": "Fichier uploadé avec succès"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@files_bp.route("/download/<int:file_id>")
def download(file_id):
    try:
        decrypted, file = FileService.download(file_id, SessionUser.user_id())
        return send_file(decrypted, as_attachment=True, download_name=file["file_name"])
    except PermissionError:
        abort(403)
    except FileNotFoundError:
        abort(404)

# ─── Partage / retrait ───────────────────────────────────────────────────────
@files_bp.route("/share", methods=["POST"])
def share():
    data    = request.get_json()
    file_id = data.get("file_id")
    user_id = data.get("user_id")
    add     = data.get("add", True)

    file = get_file_by_id(file_id)
    if not file or file["user_id"] != SessionUser.user_id():
        return jsonify({"error": "Non autorisé"}), 403

    if add:
        add_file_share(
            file_id=file_id,
            shared_by_user_id=SessionUser.user_id(),
            shared_with_user_id=user_id,
        )
        return jsonify({"message": "Partagé ✓"})
    else:
        remove_file_share(file_id=file_id, shared_with_user_id=user_id)
        return jsonify({"message": "Accès retiré"})


# ─── Suppression ─────────────────────────────────────────────────────────────
@files_bp.route("/<int:file_id>", methods=["DELETE"])
def delete(file_id):
    file = get_file_by_id(file_id)
    if not file or file["user_id"] != SessionUser.user_id():
        return jsonify({"error": "Non autorisé"}), 403

    stored = file.get("stored_filename")
    if stored:
        file_path = os.path.join(UPLOAD_FOLDER, stored)
        if os.path.isfile(file_path):
            os.remove(file_path)

    delete_file(file_id)
    return jsonify({"message": "Fichier supprimé"})