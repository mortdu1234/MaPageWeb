from flask import jsonify, render_template
from app.core.db.backend.database import get_all_from_table, get_all_tables, execute_query
from app.core.utils.sessionUser import SessionUser
from app.core.utils.routesHelper import require_permission
from app.core.utils.blueprints import make_blueprint

db_reader_bp = make_blueprint('databaseReader', __name__, __file__, "/databaseReader")

import logging
from flask import request

logger = logging.getLogger("sql_console")

@db_reader_bp.route('/query', methods=['POST'])
@require_permission("admin")
def run_query():
    payload = request.get_json(silent=True) or {}
    sql = payload.get("sql", "")

    if not isinstance(sql, str) or not sql.strip():
        return jsonify({"error": "Requête SQL vide."}), 400

    user = SessionUser.username  # adapte selon ton API existante
    logger.info(f"[SQL_CONSOLE] user={getattr(user, 'id', '?')} sql={sql!r}")

    result, error = execute_query(sql)
    if error:
        logger.warning(f"[SQL_CONSOLE] échec user={getattr(user, 'id', '?')} error={error}")
        return jsonify({"error": error}), 400

    return jsonify(result)
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