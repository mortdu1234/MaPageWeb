"""
routes/tasks.py
Blueprint Flask pour la gestion des tâches.

Endpoints :
  GET  /tasks                          → page HTML
  GET  /api/tasks                      → liste des tâches de l'user connecté
  POST /api/tasks                      → créer une tâche
  PATCH /api/tasks/<id>/toggle         → inverser done
  DELETE /api/tasks/<id>               → supprimer (owner uniquement)
  GET  /api/tasks/users                → liste des users pour la modale partage
  POST /api/tasks/<id>/share           → partager avec un user
  DELETE /api/tasks/<id>/share/<uid>   → retirer le partage
"""

from flask import Blueprint, jsonify, render_template, request

from sessionUser import SessionUser
import db.tasks as db_tasks

tasks_bp = Blueprint("tasks", __name__)


# ─── Guard : utilisateur connecté ─────────────────────────────────────────────

def _require_login():
    """Retourne (user_id, None) si connecté, sinon (None, réponse 401)."""
    if not SessionUser.is_logged_in():
        return None, (jsonify({"error": "Non authentifié"}), 401)
    return SessionUser.user_id(), None


# ─── Page HTML ────────────────────────────────────────────────────────────────

@tasks_bp.route("/tasks")
def tasks_page():
    if not SessionUser.is_logged_in():
        return render_template("login.html"), 401   # ou redirect selon ton app
    return render_template("tasks.html")


# ─── API : tâches ─────────────────────────────────────────────────────────────

@tasks_bp.route("/api/tasks", methods=["GET"])
def api_get_tasks():
    user_id, err = _require_login()
    if err:
        return err

    tasks = db_tasks.get_tasks_for_user(user_id)
    return jsonify(tasks)


@tasks_bp.route("/api/tasks", methods=["POST"])
def api_create_task():
    user_id, err = _require_login()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "Le texte ne peut pas être vide"}), 400
    if len(text) > 200:
        return jsonify({"error": "Texte trop long (200 caractères max)"}), 400

    task = db_tasks.create_task(owner_id=user_id, text=text)
    return jsonify(task), 201


@tasks_bp.route("/api/tasks/<int:task_id>/toggle", methods=["PATCH"])
def api_toggle_task(task_id: int):
    user_id, err = _require_login()
    if err:
        return err

    if not db_tasks.user_can_write(task_id, user_id):
        return jsonify({"error": "Accès refusé"}), 403

    new_done = db_tasks.toggle_task_done(task_id)
    if new_done is None:
        return jsonify({"error": "Tâche introuvable"}), 404

    return jsonify({"id": task_id, "done": new_done})


@tasks_bp.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def api_delete_task(task_id: int):
    user_id, err = _require_login()
    if err:
        return err

    if not db_tasks.user_is_owner(task_id, user_id):
        return jsonify({"error": "Seul le propriétaire peut supprimer cette tâche"}), 403

    deleted = db_tasks.delete_task(task_id)
    if not deleted:
        return jsonify({"error": "Tâche introuvable"}), 404

    return jsonify({"success": True})


# ─── API : partage ────────────────────────────────────────────────────────────

@tasks_bp.route("/api/tasks/users", methods=["GET"])
def api_get_users():
    """Retourne tous les utilisateurs (sauf l'user connecté) pour la modale."""
    user_id, err = _require_login()
    if err:
        return err

    users = db_tasks.get_all_users_except(user_id)
    return jsonify(users)


@tasks_bp.route("/api/tasks/<int:task_id>/share", methods=["POST"])
def api_share_task(task_id: int):
    user_id, err = _require_login()
    if err:
        return err

    if not db_tasks.user_is_owner(task_id, user_id):
        return jsonify({"error": "Seul le propriétaire peut partager cette tâche"}), 403

    data       = request.get_json(silent=True) or {}
    target_uid = data.get("user_id")
    permission = data.get("permission", "read")

    if not target_uid:
        return jsonify({"error": "user_id manquant"}), 400
    if permission not in ("read", "write"):
        return jsonify({"error": "permission invalide (read | write)"}), 400
    if target_uid == user_id:
        return jsonify({"error": "Impossible de partager avec soi-même"}), 400

    db_tasks.share_task(task_id, target_uid, permission)
    return jsonify({"success": True, "task_id": task_id, "user_id": target_uid, "permission": permission})


@tasks_bp.route("/api/tasks/<int:task_id>/share/<int:target_uid>", methods=["DELETE"])
def api_unshare_task(task_id: int, target_uid: int):
    user_id, err = _require_login()
    if err:
        return err

    if not db_tasks.user_is_owner(task_id, user_id):
        return jsonify({"error": "Seul le propriétaire peut gérer les partages"}), 403

    deleted = db_tasks.unshare_task(task_id, target_uid)
    if not deleted:
        return jsonify({"error": "Partage introuvable"}), 404

    return jsonify({"success": True})