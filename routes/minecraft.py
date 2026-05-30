"""
routes/minecraft.py
─────────────────────────────────────────────────────────────────────────────
Blueprint Flask pour la gestion des serveurs Minecraft via Pterodactyl.

Routes HTML (pages Jinja2)
  GET  /minecraft/                         → hub (liste des serveurs)
  GET  /minecraft/<server_id>              → page détail d'un serveur

Routes API JSON  (préfixe /minecraft/api/)
  GET  /minecraft/api/getServers                              → liste + ressources
  POST /minecraft/api/start                                   → démarrer un serveur
  POST /minecraft/api/stop                                    → arrêter un serveur
  GET  /minecraft/api/servers/<id>                            → infos statiques
  GET  /minecraft/api/servers/<id>/resources                  → métriques live
  POST /minecraft/api/servers/<id>/power                      → start/stop/restart/kill
  GET  /minecraft/api/servers/<id>/allocations                → allocations réseau
  GET  /minecraft/api/servers/<id>/backups                    → liste des sauvegardes
  POST /minecraft/api/servers/<id>/backups                    → créer une sauvegarde

Route WebSocket  (enregistrée dans app.py via register_ws)
  WS   /ws/servers/<id>/console            → proxy console bidirectionnel
"""

import logging
import threading
from functools import wraps

from flask import Blueprint, jsonify, render_template, request, abort
import requests

from backend.minecraft import API, PterodactyleAPI

log = logging.getLogger(__name__)

minecraft_bp = Blueprint("minecraft", __name__, url_prefix="/minecraft")


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
        except Exception as e:
            log.exception("Unexpected error in minecraft route")
            return jsonify({"error": "Erreur interne serveur"}), 500
    return wrapper


# ══════════════════════════════════════════════════════════════
#  PAGES HTML
# ══════════════════════════════════════════════════════════════

@minecraft_bp.route("/")
def hub():
    """Hub principal : affiche la liste des serveurs Minecraft."""
    return render_template("minecrafthub.html")


@minecraft_bp.route("/<server_id>")
def server_detail(server_id: str):
    """Page de détail d'un serveur.
    Les données sont chargées côté JS via les routes /minecraft/api/servers/<id>/...
    """
    return render_template("errors/404.html")
    return render_template("minecraftserver.html", server_id=server_id)


# ══════════════════════════════════════════════════════════════
#  API — HUB  (/minecraft/api/...)
# ══════════════════════════════════════════════════════════════

@minecraft_bp.get("/api/getServers")
@api_route
def get_servers():
    data = API.get_servers()
    return jsonify(data)


@minecraft_bp.post("/api/start")
@api_route
def start_server():
    body = request.get_json(silent=True) or {}
    server_id = body.get("id")
    if not server_id:
        abort(400)
    API.start_server(server_id)
    return jsonify({"success": True, "error": None})


@minecraft_bp.post("/api/stop")
@api_route
def stop_server():
    body = request.get_json(silent=True) or {}
    server_id = body.get("id")
    if not server_id:
        abort(400)
    API.stop_server(server_id)
    return jsonify({"success": True, "error": None})

