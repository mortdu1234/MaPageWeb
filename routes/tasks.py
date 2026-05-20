from flask import Blueprint, jsonify, request

from sessionUser import SessionUser

from db.tasks import (
    db_get_tasks_and_groups,
    db_create_task,
    db_toggle_task,
    db_delete_task,
    db_get_default_group,
    db_create_group,
    db_get_groups,
    db_get_all_accessible_groups,
    db_share_group,
    db_revoke_share,
    db_delete_group,
    db_suppr_shared,
    db_move_task,
)

tasks_bp = Blueprint('tasks', __name__)


# ──────────────────────────────────────────────────────────────
#  GET /tasks
#  Retourne toutes les tâches accessibles par l'utilisateur
#  (ses propres groupes + les groupes partagés avec lui)
#  + la liste des groupes disponibles pour les selects.
#
#  Réponse :
#  {
#    "tasks": [
#      {
#        "id": 1,
#        "title": "Ma tâche",
#        "is_done": false,
#        "is_shared": false,
#        "group_id": 2,
#        "group_name": "Perso"
#      }, ...
#    ],
#    "groups": [
#      { "id": 2, "name": "Perso" }, ...
#    ]
#  }
# ──────────────────────────────────────────────────────────────
@tasks_bp.route('/api/tasks', methods=['GET'])
def get_tasks():
    result = db_get_tasks_and_groups(user_id=SessionUser.user_id())
    return jsonify(result), 200


# ──────────────────────────────────────────────────────────────
#  POST /tasks
#  Crée une nouvelle tâche dans un groupe appartenant
#  à l'utilisateur courant.
#
#  Corps JSON :
#  {
#    "title"    : "Nom de la tâche",   (obligatoire)
#    "group_id" : 3                    (obligatoire)
#  }
#
#  Réponse : la tâche créée
#  {
#    "id": 5, "title": "...", "is_done": false,
#    "is_shared": false, "group_id": 3, "group_name": "Perso"
#  }
# ──────────────────────────────────────────────────────────────

@tasks_bp.route('/api/tasks', methods=['POST'])
def create_task():
    body     = request.get_json(silent=True) or {}
    title    = (body.get('title') or '').strip()
    group_id = body.get('group_id')
    user_id  = SessionUser.user_id()

    if not title:
        return jsonify({'error': 'Le titre est obligatoire.'}), 400

    # ── Groupe par défaut si aucun groupe fourni ──
    if not group_id:
        default = db_get_default_group(user_id)
        if default is None:
            return jsonify({'error': 'Aucun groupe disponible.'}), 400
        group_id = default['id']

    task = db_create_task(
        title=title,
        group_id=int(group_id),
        owner_id=user_id,
    )

    if task is None:
        return jsonify({'error': 'Groupe invalide ou accès refusé.'}), 403

    return jsonify(task), 201

# ──────────────────────────────────────────────────────────────
#  POST /tasks/<task_id>/toggle
#  Met à jour le champ is_done d'une tâche.
#  L'utilisateur doit avoir accès au groupe de la tâche.
#
#  Corps JSON :
#  { "is_done": true }
#
#  Réponse :
#  { "success": true }
# ──────────────────────────────────────────────────────────────
@tasks_bp.route('/api/tasks/<int:task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    body    = request.get_json(silent=True) or {}
    is_done = body.get('is_done')

    if is_done is None or not isinstance(is_done, bool):
        return jsonify({'error': 'is_done (boolean) est obligatoire.'}), 400

    ok = db_toggle_task(
        task_id=task_id,
        is_done=is_done,
        user_id=SessionUser.user_id(),
    )

    if not ok:
        return jsonify({'error': 'Tâche introuvable ou accès refusé.'}), 403

    return jsonify({'success': True}), 200


# ──────────────────────────────────────────────────────────────
#  DELETE /tasks/<task_id>
#  Supprime une tâche.
#  L'utilisateur doit être propriétaire du groupe de la tâche.
#
#  Réponse :
#  { "success": true }
# ──────────────────────────────────────────────────────────────
@tasks_bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    ok = db_delete_task(
        task_id=task_id,
        owner_id=SessionUser.user_id(),
    )

    if not ok:
        return jsonify({'error': 'Tâche introuvable ou accès refusé.'}), 403

    return jsonify({'success': True}), 200

# ──────────────────────────────────────────────────────────────
#  POST /api/groups
#  Crée un nouveau groupe appartenant à l'utilisateur courant.
#
#  Corps JSON : { "name": "Mon groupe" }
#  Réponse    : { "id": 4, "name": "Mon groupe" }
# ──────────────────────────────────────────────────────────────
# Dans tasks.py, modifie la route create_group :
@tasks_bp.route('/api/groups', methods=['GET', 'POST'])
def create_group():
    if request.method == 'GET':
        groups = db_get_all_accessible_groups(user_id=SessionUser.user_id())
        return jsonify({'groups': groups}), 200

    # POST — code existant inchangé
    body = request.get_json(silent=True) or {}
    name = (body.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Le nom est obligatoire.'}), 400
    group = db_create_group(name=name, owner_id=SessionUser.user_id())
    return jsonify(group), 201

@tasks_bp.route('/api/tasks/<int:task_id>/move', methods=['POST'])
def move_task(task_id):
    body         = request.get_json(silent=True) or {}
    new_group_id = body.get('group_id')

    if not new_group_id:
        return jsonify({'error': 'group_id est obligatoire.'}), 400

    ok = db_move_task(
        task_id=task_id,
        new_group_id=int(new_group_id),
        user_id=SessionUser.user_id(),
    )

    if not ok:
        return jsonify({'error': 'Tâche ou groupe invalide.'}), 403

    return jsonify({'success': True}), 200


# Dans le blueprint users (ou tasks.py si tu n'as pas de blueprint users)
@tasks_bp.route('/api/users', methods=['GET'])
def get_users():
    from db.users import get_all_users
    users = get_all_users()
    return jsonify({'users': users}), 200

# POST /api/groups/<group_id>/share
@tasks_bp.route('/api/groups/<int:group_id>/share', methods=['POST'])
def share_group(group_id):
    body    = request.get_json(silent=True) or {}
    user_id = body.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id est obligatoire.'}), 400

    ok = db_share_group(
        group_id=group_id,
        target_user_id=int(user_id),
        owner_id=SessionUser.user_id(),
    )
    if not ok:
        return jsonify({'error': 'Groupe invalide ou accès refusé.'}), 403
    return jsonify({'success': True}), 201


# DELETE /api/groups/<group_id>/share/<user_id>
@tasks_bp.route('/api/groups/<int:group_id>/share/<int:user_id>', methods=['DELETE'])
def revoke_share(group_id, user_id):
    ok = db_revoke_share(
        group_id=group_id,
        target_user_id=user_id,
        owner_id=SessionUser.user_id(),
    )
    if not ok:
        return jsonify({'error': 'Accès refusé.'}), 403
    return jsonify({'success': True}), 200

        
@tasks_bp.route('/api/groups/<int:group_id>', methods=['DELETE'])
def delete_group(group_id):
    ok = db_delete_group(
        group_id=group_id,
        owner_id=SessionUser.user_id(),
    )
    if not ok:
        return jsonify({'error': 'Groupe introuvable ou accès refusé.'}), 403
    return jsonify({'success': True}), 200

@tasks_bp.route('/api/groups/<int:group_id>/leave', methods=['DELETE'])
def leave_shared_group(group_id):
    user_id = SessionUser.user_id()
    print(f"quitter un groupe groupeID:{group_id} userID:{user_id}")
    res = db_suppr_shared(group_id, user_id)
    if res:
        return jsonify({'success': True}), 200
    return jsonify({'error': 'Partage introuvable.'}), 404