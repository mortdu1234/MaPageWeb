from flask import jsonify, render_template
from app.core.db.backend.database import get_all_from_table, get_all_tables
from app.core.utils.sessionUser import SessionUser
from app.core.utils.routesHelper import require_permission
from app.core.utils.blueprints import make_blueprint

db_reader_bp = make_blueprint('databaseReader', __name__, __file__, "/databaseReader")


# ─── Page HTML ────────────────────────────────────────────────────────────────

@db_reader_bp.route('/')
@require_permission("showDatabase")
def database_page():
    tables = get_all_tables()
    return render_template(db_reader_bp.get_templates_path('database.html'), tables=tables)


@db_reader_bp.route('/<string:table_name>')
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