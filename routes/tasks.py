"""
routes/tasks.py
Blueprint Flask pour la gestion des tâches et des groupes.

Endpoints tâches :
  GET    /tasks                          → page HTML
  GET    /api/tasks                      → liste des tâches de l'user connecté
  POST   /api/tasks                      → créer une tâche  { text, group_id? }
  PATCH  /api/tasks/<id>/toggle          → inverser done
  PATCH  /api/tasks/<id>/group           → changer le groupe  { group_id: int|null }
  DELETE /api/tasks/<id>                 → supprimer (owner uniquement)
  GET    /api/tasks/users                → liste des users pour la modale partage
  POST   /api/tasks/<id>/share           → partager avec un user
  DELETE /api/tasks/<id>/share/<uid>     → retirer le partage

Endpoints groupes :
  GET    /api/groups                     → liste des groupes de l'user
  POST   /api/groups                     → créer un groupe  { name, color? }
  PATCH  /api/groups/<id>                → modifier  { name?, color? }
  DELETE /api/groups/<id>                → supprimer (les tâches passent à group_id=null)
  POST   /api/groups/reorder             → réordonner  { ordered_ids: [int] }
  GET    /api/groups/<id>/shares         → liste des partages d'un groupe
  POST   /api/groups/<id>/share          → partager un groupe  { user_id, permission? }
  DELETE /api/groups/<id>/share/<uid>    → retirer le partage d'un groupe
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
        return render_template("login.html"), 401
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

    data     = request.get_json(silent=True) or {}
    text     = (data.get("text") or "").strip()
    group_id = data.get("group_id")  # int ou None

    if not text:
        return jsonify({"error": "Le texte ne peut pas être vide"}), 400
    if len(text) > 200:
        return jsonify({"error": "Texte trop long (200 caractères max)"}), 400

    # Le groupe doit appartenir à l'user OU être partagé avec lui en écriture
    if group_id is not None:
        if not isinstance(group_id, int):
            return jsonify({"error": "group_id invalide"}), 400
        if not db_tasks.group_accessible_by(group_id, user_id):
            return jsonify({"error": "Groupe introuvable"}), 404

    task = db_tasks.create_task(owner_id=user_id, text=text, group_id=group_id)
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


@tasks_bp.route("/api/tasks/<int:task_id>/group", methods=["PATCH"])
def api_set_task_group(task_id: int):
    """Assigne ou retire un groupe d'une tâche. Requiert permission write ou owner."""
    user_id, err = _require_login()
    if err:
        return err

    if not db_tasks.user_can_write(task_id, user_id):
        return jsonify({"error": "Accès refusé"}), 403

    data     = request.get_json(silent=True) or {}
    group_id = data.get("group_id")  # int ou None (explicitement null pour retirer)

    if group_id is not None:
        if not isinstance(group_id, int):
            return jsonify({"error": "group_id invalide"}), 400
        # Le groupe doit appartenir au propriétaire de la tâche
        task = db_tasks.get_task_by_id(task_id)
        if not task:
            return jsonify({"error": "Tâche introuvable"}), 404
        if not db_tasks.group_belongs_to(group_id, task["owner_id"]):
            return jsonify({"error": "Groupe introuvable"}), 404

    updated = db_tasks.set_task_group(task_id, group_id)
    if not updated:
        return jsonify({"error": "Tâche introuvable"}), 404

    return jsonify({"id": task_id, "group_id": group_id})


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


# ─── API : partage de tâches ──────────────────────────────────────────────────

@tasks_bp.route("/api/tasks/users", methods=["GET"])
def api_get_users():
    """Retourne tous les utilisateurs (sauf l'user connecté) pour les modales."""
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


# ─── API : groupes ────────────────────────────────────────────────────────────

@tasks_bp.route("/api/groups", methods=["GET"])
def api_get_groups():
    user_id, err = _require_login()
    if err:
        return err

    groups = db_tasks.get_groups_for_user(user_id)
    return jsonify(groups)


@tasks_bp.route("/api/groups", methods=["POST"])
def api_create_group():
    user_id, err = _require_login()
    if err:
        return err

    data  = request.get_json(silent=True) or {}
    name  = (data.get("name") or "").strip()
    color = data.get("color", "#b89a6a")

    if not name:
        return jsonify({"error": "Le nom ne peut pas être vide"}), 400
    if len(name) > 60:
        return jsonify({"error": "Nom trop long (60 caractères max)"}), 400
    if not isinstance(color, str) or not color.startswith("#") or len(color) not in (4, 7):
        color = "#b89a6a"

    try:
        group = db_tasks.create_group(owner_id=user_id, name=name, color=color)
    except Exception:
        # Contrainte UNIQUE (owner_id, name)
        return jsonify({"error": "Un groupe avec ce nom existe déjà"}), 409

    return jsonify(group), 201


@tasks_bp.route("/api/groups/<int:group_id>", methods=["PATCH"])
def api_update_group(group_id: int):
    user_id, err = _require_login()
    if err:
        return err

    if not db_tasks.group_belongs_to(group_id, user_id):
        return jsonify({"error": "Groupe introuvable"}), 404

    data  = request.get_json(silent=True) or {}
    name  = (data.get("name") or "").strip() or None
    color = data.get("color")

    if color is not None:
        if not isinstance(color, str) or not color.startswith("#") or len(color) not in (4, 7):
            return jsonify({"error": "Couleur invalide (format #rrggbb ou #rgb)"}), 400

    if name is None and color is None:
        return jsonify({"error": "Aucun champ à mettre à jour"}), 400
    if name and len(name) > 60:
        return jsonify({"error": "Nom trop long (60 caractères max)"}), 400

    try:
        group = db_tasks.update_group(group_id, name=name, color=color)
    except Exception:
        return jsonify({"error": "Un groupe avec ce nom existe déjà"}), 409

    if not group:
        return jsonify({"error": "Groupe introuvable"}), 404

    return jsonify(group)


@tasks_bp.route("/api/groups/<int:group_id>", methods=["DELETE"])
def api_delete_group(group_id: int):
    user_id, err = _require_login()
    if err:
        return err

    if not db_tasks.group_belongs_to(group_id, user_id):
        return jsonify({"error": "Groupe introuvable"}), 404

    db_tasks.delete_group(group_id)
    return jsonify({"success": True})


@tasks_bp.route("/api/groups/reorder", methods=["POST"])
def api_reorder_groups():
    user_id, err = _require_login()
    if err:
        return err

    data        = request.get_json(silent=True) or {}
    ordered_ids = data.get("ordered_ids", [])

    if not isinstance(ordered_ids, list) or not all(isinstance(i, int) for i in ordered_ids):
        return jsonify({"error": "ordered_ids doit être une liste d'entiers"}), 400

    db_tasks.reorder_groups(user_id, ordered_ids)
    return jsonify({"success": True})


# ─── API : partage de groupes ─────────────────────────────────────────────────

@tasks_bp.route("/api/groups/<int:group_id>/shares", methods=["GET"])
def api_get_group_shares(group_id: int):
    """Retourne la liste des utilisateurs avec qui le groupe est partagé."""
    user_id, err = _require_login()
    if err:
        return err

    if not db_tasks.group_belongs_to(group_id, user_id):
        return jsonify({"error": "Groupe introuvable"}), 404

    shares = db_tasks.get_group_shares(group_id)
    return jsonify(shares)


@tasks_bp.route("/api/groups/<int:group_id>/share", methods=["POST"])
def api_share_group(group_id: int):
    """Partage un groupe avec un autre utilisateur. Réservé au propriétaire."""
    user_id, err = _require_login()
    if err:
        return err

    if not db_tasks.group_belongs_to(group_id, user_id):
        return jsonify({"error": "Groupe introuvable"}), 404

    data       = request.get_json(silent=True) or {}
    target_uid = data.get("user_id")
    permission = data.get("permission", "read")

    if not target_uid:
        return jsonify({"error": "user_id manquant"}), 400
    if permission not in ("read", "write"):
        return jsonify({"error": "permission invalide (read | write)"}), 400
    if target_uid == user_id:
        return jsonify({"error": "Impossible de partager avec soi-même"}), 400

    db_tasks.share_group(group_id, target_uid, permission)
    return jsonify({
        "success":    True,
        "group_id":   group_id,
        "user_id":    target_uid,
        "permission": permission,
    })


@tasks_bp.route("/api/groups/<int:group_id>/share/<int:target_uid>", methods=["DELETE"])
def api_unshare_group(group_id: int, target_uid: int):
    """Retire le partage d'un groupe pour un utilisateur. Réservé au propriétaire."""
    user_id, err = _require_login()
    if err:
        return err

    if not db_tasks.group_belongs_to(group_id, user_id):
        return jsonify({"error": "Groupe introuvable"}), 404

    deleted = db_tasks.unshare_group(group_id, target_uid)
    if not deleted:
        return jsonify({"error": "Partage introuvable"}), 404

    return jsonify({"success": True})