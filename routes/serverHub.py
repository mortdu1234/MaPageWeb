"""
routes/serverhub.py
─────────────────────────────────────────────────────────────────────────────
Blueprint Flask pour la gestion des serveurs de jeu (Minecraft, Palworld, ...)
via Pterodactyl.

Routes HTML (pages Jinja2)
  GET  /serverhub/                                → hub (liste des serveurs)
  GET  /serverhub/<server_id>                      → page détail d'un serveur

Routes API JSON  (préfixe /serverhub/api/)
  GET  /serverhub/api/getServers                       → liste + ressources live
  GET  /serverhub/api/servers/<id>                      → infos statiques + game_info
  GET  /serverhub/api/servers/<id>/resources            → métriques live
  POST /serverhub/api/servers/<id>/power                → start/stop/restart/kill
  GET  /serverhub/api/servers/<id>/allocations          → allocations réseau
  GET  /serverhub/api/servers/<id>/backups              → liste des sauvegardes
  POST /serverhub/api/servers/<id>/backups              → créer une sauvegarde
  POST /serverhub/api/start                             → (legacy, voir plus bas)
  POST /serverhub/api/stop                              → (legacy, voir plus bas)

Route WebSocket  (enregistrée dans app.py via register_ws)
  WS   /ws/servers/<id>/console
       → proxy console bidirectionnel, s'appuie sur
         ServerManager.get_server(id).get_websocket_client()
"""

import logging
from functools import wraps

from flask import Blueprint, jsonify, render_template, request, abort
import requests

from backend.ServersGestions.manager import ServerManager

log = logging.getLogger(__name__)

serverhub_bp = Blueprint("serverhub", __name__, url_prefix="/serverhub")

_ALLOWED_SIGNALS = {"start", "stop", "restart", "kill"}


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def api_route(f):
    """Décorateur : transforme les exceptions en réponses JSON propres."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else 502
            log.warning("Pterodactyl HTTP error %s: %s", status, e)
            return jsonify({"error": str(e)}), status
        except requests.ConnectionError:
            log.error("Cannot reach Pterodactyl panel")
            return jsonify({"error": "Panel injoignable"}), 502
        except requests.Timeout:
            return jsonify({"error": "Timeout panel"}), 504
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception:
            log.exception("Unexpected error in serverhub route")
            return jsonify({"error": "Erreur interne serveur"}), 500
    return wrapper


# ══════════════════════════════════════════════════════════════
#  PAGES HTML
# ══════════════════════════════════════════════════════════════

@serverhub_bp.route("/")
def hub():
    """Hub principal : affiche la liste de tous les serveurs (Minecraft, Palworld, ...)."""
    return render_template("serverhub.html")


@serverhub_bp.route("/<server_id>")
def server_detail(server_id: str):
    """Page de détail d'un serveur.
    Les données sont chargées côté JS via les routes /serverhub/api/servers/<id>/...
    """
    return render_template("errors/404.html")
    return render_template("serverdetail.html", server_id=server_id)


# ══════════════════════════════════════════════════════════════
#  API — HUB  (/serverhub/api/...)
# ══════════════════════════════════════════════════════════════

@serverhub_bp.get("/api/getServers")
@api_route
def get_servers():
    data = ServerManager.get_servers()
    return jsonify(data)


# ══════════════════════════════════════════════════════════════
#  API — SERVEUR UNIQUE  (/serverhub/api/servers/<id>/...)
# ══════════════════════════════════════════════════════════════

@serverhub_bp.get("/api/servers/<server_id>")
@api_route
def get_server_info(server_id: str):
    server = ServerManager.get_server(server_id)
    return jsonify(server.get_info())


@serverhub_bp.get("/api/servers/<server_id>/resources")
@api_route
def get_server_resources(server_id: str):
    server = ServerManager.get_server(server_id)
    return jsonify(server.get_resources())


@serverhub_bp.post("/api/servers/<server_id>/power")
@api_route
def power_server(server_id: str):
    """Body attendu : {"signal": "start" | "stop" | "restart" | "kill"}"""
    body = request.get_json(silent=True) or {}
    signal = body.get("signal")
    if signal not in _ALLOWED_SIGNALS:
        raise ValueError(f"Signal invalide, attendu l'un de {sorted(_ALLOWED_SIGNALS)}")

    server = ServerManager.get_server(server_id)
    getattr(server, signal)()  # server.start() / .stop() / .restart() / .kill()
    return jsonify({"success": True, "error": None})


@serverhub_bp.get("/api/servers/<server_id>/allocations")
@api_route
def get_server_allocations(server_id: str):
    server = ServerManager.get_server(server_id)
    return jsonify(server.get_allocations())


@serverhub_bp.get("/api/servers/<server_id>/backups")
@api_route
def get_server_backups(server_id: str):
    server = ServerManager.get_server(server_id)
    return jsonify(server.get_backups())


@serverhub_bp.post("/api/servers/<server_id>/backups")
@api_route
def create_server_backup(server_id: str):
    server = ServerManager.get_server(server_id)
    return jsonify(server.create_backup())


# ══════════════════════════════════════════════════════════════
#  API — LEGACY
#  Conservées pour compat avec l'existant (serverhub.html utilise encore
#  /api/start et /api/stop). Remplaçables par /api/servers/<id>/power une fois
#  le frontend migré — voir minecraftServerCard.js.
# ══════════════════════════════════════════════════════════════

@serverhub_bp.post("/api/start")
@api_route
def start_server():
    body = request.get_json(silent=True) or {}
    server_id = body.get("id")
    if not server_id:
        abort(400)
    ServerManager.get_server(server_id).start()
    return jsonify({"success": True, "error": None})


@serverhub_bp.post("/api/stop")
@api_route
def stop_server():
    body = request.get_json(silent=True) or {}
    server_id = body.get("id")
    if not server_id:
        abort(400)
    ServerManager.get_server(server_id).stop()
    return jsonify({"success": True, "error": None})