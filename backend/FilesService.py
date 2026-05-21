import uuid
import os
from crypto import encrypt_file, decrypt_file
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
from config import Config

class FileService:
    @staticmethod
    def upload(file, user_id) -> int:
        """Chiffre, stocke sur disque, enregistre en BDD."""
        ext = os.path.splitext(file.filename)[1]
        stored_filename = f"{uuid.uuid4().hex}{ext}.enc"
        file_path = os.path.join(Config.UPLOAD_FOLDER, stored_filename)
        encrypt_file(file.read(), file_path)
        return add_new_file(file.filename, stored_filename, user_id)

    @staticmethod
    def download(file_id, user_id):
        """Vérifie les droits, déchiffre et retourne les bytes."""
        file = get_file_by_id(file_id)
        if not file:
            raise FileNotFoundError()

        shared_ids = [f["id"] for f in get_files_shared_with_user(user_id)]
        if file["user_id"] != user_id and file_id not in shared_ids:
            raise PermissionError()

        return decrypt_file(os.path.join(Config.UPLOAD_FOLDER, file["stored_filename"])), file

    @staticmethod
    def delete(file_id, user_id):
        """Vérifie les droits, supprime disque + BDD."""
        file = get_file_by_id(file_id)
        if not file or file["user_id"] != user_id:
            raise PermissionError()

        path = os.path.join(Config.UPLOAD_FOLDER, file["stored_filename"])
        if os.path.isfile(path):
            os.remove(path)
        delete_file(file_id)