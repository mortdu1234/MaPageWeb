from flask import Blueprint, render_template, request, jsonify
from routes import require_permission
from backend.notifications import notifier

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/apropos")
def apropos():
    return render_template("apropos.html")


@main_bp.route("/contact")
def contact():
    return render_template("contact.html")

@main_bp.route("/contact/send", methods=["POST"])
def sendMail():
    data = request.get_json()
    
    nom     = data.get('nom', '').strip()
    email   = data.get('email', '').strip()
    message = data.get('message', '').strip()

    success = notifier(f"Mail de:{nom}", f"from:{email}\nmessage:\n{message}", "high", ["Contact"])
    if success:
        return jsonify({'success': True, 'error': ''}), 200
    return jsonify({'success': False, 'error': 'Champs manquants'}), 500
    



@main_bp.route("/tasks")
def tasks():
    return render_template("tasks.html")
