from flask import render_template, request, jsonify

from app.core.utils.blueprints import make_blueprint
from app.core.db.backend.permissions import get_permissions_matrix, grant_permission, revoke_permission

permissions_bp = make_blueprint("permissions", __name__, __file__, url_prefix=None)


@permissions_bp.route("/permissions")
def permissions_page():
    users, permissions, granted_set = get_permissions_matrix()
    return render_template(
        permissions_bp.get_templates_path("adminGestion.html"),
        users=users,
        permissions=permissions,
        granted_set=granted_set,
    )


@permissions_bp.route("/permissions/toggle", methods=["POST"])
def toggle_permission():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    permission_id = data.get("permission_id")
    granted = data.get("granted")

    if user_id is None or permission_id is None or granted is None:
        return jsonify({"success": False, "error": "Paramètres manquants"}), 400

    try:
        user_id = int(user_id)
        permission_id = int(permission_id)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Paramètres invalides"}), 400

    try:
        if granted:
            grant_permission(user_id, permission_id, granted_by=1)
        else:
            revoke_permission(user_id, permission_id)
        return jsonify({"success": True, "error": ""}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500