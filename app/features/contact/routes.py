from flask import render_template, request, jsonify

from app.core.utils.blueprints import make_blueprint

contact_bp = make_blueprint("contact", __name__, __file__, url_prefix=None)

@contact_bp.route("/contact")
def contact():
    return render_template(contact_bp.get_templates_path("contact.html"))


@contact_bp.route("/contact/send", methods=["POST"])
def send_mail():
    data = request.get_json()
    nom = data.get("nom", "").strip()
    email = data.get("email", "").strip()
    message = data.get("message", "").strip()

    # success = notifier(f"Mail de:{nom}", f"from:{email}\nmessage:\n{message}", "high", ["Contact"])
    # if success:
    #     return jsonify({'success': True, 'error': ''}), 200
    return jsonify({"success": False, "error": "Champs manquants"}), 500