"""
routes/api_database.py
Blueprint Flask pour la page et l'API "Database".

Routes :
  GET /database               → page HTML (liste des tables injectée via Jinja2)
  GET /api/database/<table>   → données JSON d'une table
"""

from flask import Blueprint, jsonify, render_template
from db.database import get_all_from_table, get_all_tables
from sessionUser import SessionUser

api_db_bp = Blueprint('api_database', __name__)


# ─── Page HTML ────────────────────────────────────────────────────────────────

@api_db_bp.route('/database')
def database_page():
    tables = get_all_tables()
    return render_template('database.html', tables=tables)


# ─── API JSON ─────────────────────────────────────────────────────────────────

@api_db_bp.route('/api/database/<string:table_name>')
def get_table_data(table_name: str):
    """
    Retourne toutes les lignes d'une table autorisée.
    Réponse JSON : { "columns": [...], "rows": [{col: val, ...}, ...] }
    """
    if not SessionUser.is_logged_in():
        return jsonify({"error": "Non authentifié"}), 401

    data, error = get_all_from_table(table_name)
    if error:
        return jsonify({"error": error}), 400

    return jsonify(data)