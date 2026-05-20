"""
db/
Couche d'accès à la base de données.

Usage depuis n'importe quelle route :
    from db.users import get_user_by_username
    from db.permissions import get_user_permissions
"""
import psycopg2.pool
from config import Config

_pool = None

def init_pool():
    global _pool
    try:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,   # connexions toujours ouvertes
            maxconn=10,  # maximum simultané
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            connect_timeout=5,
            options="-c client_encoding=UTF8"
        )
    except Exception as exc:
        raise RuntimeError(
            f"[DB] Impossible de se connecter à PostgreSQL {Config.DB_HOST}:{Config.DB_PORT} : {exc}"
        ) from exc

def get_db():
    return _pool.getconn()

def release_db(conn):
    _pool.putconn(conn)