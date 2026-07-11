"""Routes de tâches du package app."""

from flask import Blueprint, jsonify, request

from app.core.auth import SessionUser
from db.tasks import (
    db_create_group,
    db_create_task,
    db_delete_group,
    db_delete_task,
    db_get_all_accessible_groups,
    db_get_default_group,
    db_get_groups,
    db_get_tasks_and_groups,
    db_move_task,
    db_revoke_share,
    db_share_group,
    db_suppr_shared,
    db_toggle_task,
)


tasks_bp = Blueprint(
    "tasks",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/tasks/static",
)


@tasks_bp.route("/api/tasks", methods=["GET"])
def get_tasks():
    result = db_get_tasks_and_groups(user_id=SessionUser.user_id())
    return jsonify(result), 200


@tasks_bp.route("/api/tasks", methods=["POST"])
def create_task():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    group_id = body.get("group_id")
    user_id = SessionUser.user_id()

    if not title:
        return jsonify({"error": "Le titre est obligatoire."}), 400

    if not group_id:
        default = db_get_default_group(user_id)
        if default is None:
            return jsonify({"error": "Aucun groupe disponible."}), 400
        group_id = default["id"]

    task = db_create_task(title=title, group_id=int(group_id), owner_id=user_id)

    if task is None:
        return jsonify({"error": "Groupe invalide ou accès refusé."}), 403

    return jsonify(task), 201


@tasks_bp.route("/api/tasks/<int:task_id>/toggle", methods=["POST"])
def toggle_task(task_id):
    body = request.get_json(silent=True) or {}
    is_done = body.get("is_done")

    if is_done is None or not isinstance(is_done, bool):
        return jsonify({"error": "is_done (boolean) est obligatoire."}), 400

    ok = db_toggle_task(task_id=task_id, is_done=is_done, user_id=SessionUser.user_id())

    if not ok:
        return jsonify({"error": "Tâche introuvable ou accès refusé."}), 403

    return jsonify({"success": True}), 200


@tasks_bp.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    ok = db_delete_task(task_id=task_id, owner_id=SessionUser.user_id())

    if not ok:
        return jsonify({"error": "Tâche introuvable ou accès refusé."}), 403

    return jsonify({"success": True}), 200


@tasks_bp.route("/api/groups", methods=["GET", "POST"])
def create_group():
    if request.method == "GET":
        groups = db_get_all_accessible_groups(user_id=SessionUser.user_id())
        return jsonify({"groups": groups}), 200

    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Le nom est obligatoire."}), 400
    group = db_create_group(name=name, owner_id=SessionUser.user_id())
    return jsonify(group), 201


@tasks_bp.route("/api/tasks/<int:task_id>/move", methods=["POST"])
def move_task(task_id):
    body = request.get_json(silent=True) or {}
    new_group_id = body.get("group_id")

    if not new_group_id:
        return jsonify({"error": "group_id est obligatoire."}), 400

    ok = db_move_task(task_id=task_id, new_group_id=int(new_group_id), user_id=SessionUser.user_id())

    if not ok:
        return jsonify({"error": "Tâche ou groupe invalide."}), 403

    return jsonify({"success": True}), 200


@tasks_bp.route("/api/users", methods=["GET"])
def get_users():
    from db.users import get_all_users

    users = get_all_users()
    return jsonify({"users": users}), 200


@tasks_bp.route("/api/groups/<int:group_id>/share", methods=["POST"])
def share_group(group_id):
    body = request.get_json(silent=True) or {}
    user_id = body.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id est obligatoire."}), 400

    ok = db_share_group(group_id=group_id, target_user_id=int(user_id), owner_id=SessionUser.user_id())
    if not ok:
        return jsonify({"error": "Groupe invalide ou accès refusé."}), 403
    return jsonify({"success": True}), 201


@tasks_bp.route("/api/groups/<int:group_id>/share/<int:user_id>", methods=["DELETE"])
def revoke_share(group_id, user_id):
    ok = db_revoke_share(group_id=group_id, target_user_id=user_id, owner_id=SessionUser.user_id())
    if not ok:
        return jsonify({"error": "Accès refusé."}), 403
    return jsonify({"success": True}), 200


@tasks_bp.route("/api/groups/<int:group_id>", methods=["DELETE"])
def delete_group(group_id):
    ok = db_delete_group(group_id=group_id, owner_id=SessionUser.user_id())
    if not ok:
        return jsonify({"error": "Groupe introuvable ou accès refusé."}), 403
    return jsonify({"success": True}), 200


@tasks_bp.route("/api/groups/<int:group_id>/leave", methods=["DELETE"])
def leave_shared_group(group_id):
    user_id = SessionUser.user_id()
    res = db_suppr_shared(group_id, user_id)
    if res:
        return jsonify({"success": True}), 200
    return jsonify({"error": "Partage introuvable."}), 404


__all__ = ["tasks_bp"]
