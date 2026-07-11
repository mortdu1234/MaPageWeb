"""
Routes de gestion du serveur "minijeux" Minecraft distant.

Page HTML :
  GET  /minijeux/serveur                -> affiche la page de gestion

API :
  GET  /api/minijeux/serveur/liste      -> liste des minijeux + minijeu actif
  POST /api/minijeux/serveur/switch     -> stop -> switch (SSH) -> start,
                                            réponse en streaming (text/plain)
"""

import json
import os
import time

from flask import Blueprint, Response, jsonify, render_template, request, stream_with_context

from app.features.games.services.remote_minigame import RemoteMinigameService, RemoteMinigameServiceError
from config import MINIGAME_VM_PTERODACTYL_ID
from pterodactyl.PterodactylClient import PterodactylClientWrapper

serverMinijeux_bp = Blueprint("serverMinijeux", __name__)

# États Pterodactyl attendus après un power signal (voir get_utilization()).
_STATE_OFFLINE = "offline"
_STATE_RUNNING = "running"

# Délais de polling pour attendre la fin d'un arrêt/démarrage.
_POLL_INTERVAL_SECONDS = 2
_STOP_TIMEOUT_SECONDS = 90
_START_TIMEOUT_SECONDS = 120

# Petit fichier local qui garde en mémoire le dernier minijeu activé.
# Le script distant ne renseigne pas cette info lui-même (il ne fait que
# remplacer le monde + le jar), donc on la garde côté app Flask.
# -> À remplacer par un vrai enregistrement en base si tu préfères
#    (voir db/ dans le projet).
_CURRENT_GAME_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "current_minigame.json"
)


def _read_current_game():
    try:
        with open(_CURRENT_GAME_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("name")
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _write_current_game(name):
    os.makedirs(os.path.dirname(_CURRENT_GAME_FILE), exist_ok=True)
    with open(_CURRENT_GAME_FILE, "w", encoding="utf-8") as f:
        json.dump({"name": name}, f)


class PowerActionTimeoutError(Exception):
    """Le serveur n'a pas atteint l'état attendu dans le délai imparti."""


def _get_server_state() -> str | None:
    """Lit le current_state depuis get_utilization() (format pydactyl)."""
    utilization = PterodactylClientWrapper.get_utilization(MINIGAME_VM_PTERODACTYL_ID)
    # pydactyl renvoie généralement {"attributes": {"current_state": "...", ...}}
    attributes = utilization.get("attributes", utilization) if isinstance(utilization, dict) else {}
    return attributes.get("current_state")


def _wait_for_state(target_state: str, timeout: int):
    """
    Générateur : poll l'état du serveur toutes les _POLL_INTERVAL_SECONDS et
    yield une ligne de statut à chaque vérification. Lève
    PowerActionTimeoutError si le délai est dépassé sans atteindre l'état cible.
    """
    elapsed = 0
    last_state = None
    while elapsed < timeout:
        state = _get_server_state()
        if state != last_state:
            yield f"    état actuel : {state}\n"
            last_state = state
        if state == target_state:
            return
        time.sleep(_POLL_INTERVAL_SECONDS)
        elapsed += _POLL_INTERVAL_SECONDS

    raise PowerActionTimeoutError(
        f"Le serveur n'a pas atteint l'état '{target_state}' après {timeout}s "
        f"(dernier état observé : {last_state})"
    )


@serverMinijeux_bp.route("/minijeux/serveur")
def serveur_minijeux_page():
    # À adapter : si tes autres pages passent des infos de session/permissions
    # au template (voir sessionUser.py), fais pareil ici.
    return render_template("jeux/serveurMinijeux.html")


@serverMinijeux_bp.route("/api/minijeux/serveur/liste")
def api_liste_minijeux():
    service = RemoteMinigameService()
    try:
        minigames = service.list_minigames()
    except RemoteMinigameServiceError as exc:
        return jsonify({"error": str(exc)}), 502

    return jsonify(
        {
            "minigames": minigames,
            "current": _read_current_game(),
        }
    )


@serverMinijeux_bp.route("/api/minijeux/serveur/switch", methods=["POST"])
def api_switch_minijeu():
    payload = request.get_json(silent=True) or {}
    game_name = (payload.get("name") or "").strip()
    if not game_name:
        return jsonify({"error": "Paramètre 'name' manquant"}), 400

    service = RemoteMinigameService()

    def generate():
        try:
            # 1. Arrêt du serveur
            yield "==> Arrêt du serveur en cours...\n"
            PterodactylClientWrapper.send_power_action(MINIGAME_VM_PTERODACTYL_ID, "stop")
            yield from _wait_for_state(_STATE_OFFLINE, _STOP_TIMEOUT_SECONDS)
            yield "==> Serveur arrêté.\n\n"

            # 2. Switch de map (SSH + sudo changeMap.sh sur la VM Wings)
            yield f"==> Switch vers le minijeu \"{game_name}\"...\n"
            for chunk in service.switch_game_stream(game_name):
                yield chunk
            _write_current_game(game_name)
            yield "\n"

            # 3. Redémarrage du serveur
            yield "==> Redémarrage du serveur...\n"
            PterodactylClientWrapper.send_power_action(MINIGAME_VM_PTERODACTYL_ID, "start")
            yield from _wait_for_state(_STATE_RUNNING, _START_TIMEOUT_SECONDS)

            yield "\n[OK] Switch terminé, serveur relancé avec succès.\n"
        except PowerActionTimeoutError as exc:
            yield f"\n[ERREUR] {exc}\n"
        except RemoteMinigameServiceError as exc:
            yield f"\n[ERREUR] {exc}\n"
        except Exception as exc:  # noqa: BLE001
            yield f"\n[ERREUR] Erreur inattendue : {exc}\n"

    return Response(stream_with_context(generate()), mimetype="text/plain")