"""
Route /terminal – affiche les logs Flask en temps réel.

Intégration dans ton app Flask :
  from terminal_route import terminal_bp
  app.register_blueprint(terminal_bp)

Dépendances : aucune (stdlib uniquement)
"""

import logging
import queue
import threading
from collections import deque
from flask import Blueprint, Response, render_template, stream_with_context

from routes import require_permission

terminal_bp = Blueprint("terminal", __name__)

HISTORY_SIZE = 500   # nombre de lignes conservées en mémoire

# ── Historique circulaire (500 derniers logs) ────────────────────────────────
_lock    = threading.Lock()
_history: deque = deque(maxlen=HISTORY_SIZE)   # éléments : "LEVEL|message"

# ── Abonnés actifs : chaque connexion SSE a sa propre queue ──────────────────
_subscribers: list[queue.Queue] = []


class _QueueHandler(logging.Handler):
    """Stocke chaque log dans l'historique et le pousse aux abonnés SSE."""

    LEVEL_MAP = {
        "DEBUG":    "debug",
        "INFO":     "info",
        "WARNING":  "warning",
        "ERROR":    "error",
        "CRITICAL": "critical",
    }

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg   = self.format(record)
            level = self.LEVEL_MAP.get(record.levelname, "info")
            entry = f"{level}|{msg}"          # format interne

            with _lock:
                _history.append(entry)
                dead = []
                for q in _subscribers:
                    try:
                        q.put_nowait(entry)
                    except queue.Full:
                        dead.append(q)        # client trop lent → on le retire
                for q in dead:
                    _subscribers.remove(q)
        except Exception:
            pass  # ne jamais bloquer le thread principal


# ── Installation du handler (une seule fois) ────────────────────────────────
_handler = _QueueHandler()
_handler.setFormatter(logging.Formatter(
    "[%(asctime)s] %(levelname)-8s %(name)s – %(message)s",
    datefmt="%H:%M:%S",
))

_root_logger = logging.getLogger()
if not any(isinstance(h, _QueueHandler) for h in _root_logger.handlers):
    _root_logger.addHandler(_handler)


# ── Routes ───────────────────────────────────────────────────────────────────
@terminal_bp.route("/terminal")
@require_permission("showTerminal")
def terminal_page():
    return render_template("terminal.html")


@terminal_bp.route("/terminal/stream")
@require_permission("showTerminal")
def terminal_stream():
    """
    Endpoint SSE.
    1. Envoie d'abord les 500 derniers logs (historique).
    2. Puis stream les nouveaux logs en temps réel.
    """
    client_q: queue.Queue = queue.Queue(maxsize=500)

    # Snapshot de l'historique + enregistrement de l'abonné (atomique)
    with _lock:
        snapshot = list(_history)
        _subscribers.append(client_q)

    def generate():
        # ── Replay de l'historique ──────────────────────────────
        if snapshot:
            yield f"data: system|── {len(snapshot)} ligne(s) d'historique ──\n\n"
            for entry in snapshot:
                yield f"data: {entry}\n\n"
            yield "data: system|── Fin de l'historique · logs en direct ──\n\n"
        else:
            yield "data: info|Terminal connecté – en attente de logs…\n\n"

        # ── Nouveaux logs en temps réel ─────────────────────────
        try:
            while True:
                try:
                    entry = client_q.get(timeout=15)
                    yield f"data: {entry}\n\n"
                except queue.Empty:
                    yield ": keep-alive\n\n"   # commentaire SSE (pas affiché)
        finally:
            # Nettoyage : retire l'abonné quand le client se déconnecte
            with _lock:
                try:
                    _subscribers.remove(client_q)
                except ValueError:
                    pass

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # important pour Nginx
        },
    )