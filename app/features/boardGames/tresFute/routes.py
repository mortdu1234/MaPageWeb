from flask import render_template, request, jsonify
from app.core.utils.routesHelper import require_permission
from app.core.utils.blueprints import make_blueprint

from app.core.db.backend.joueurs import get_all_joueurs, create_joueur, joueur_exists
from app.core.db.backend.parties import get_parties_by_jeu, create_partie_simple

# ⚠️ Ajuster ce chemin d'import si submit.py ne se trouve pas au même
#    endroit que routes.py (ex: app.jeux.tresFute.submit).
from .backend.submit import submit_score

tresFute_bp = make_blueprint("tresFute", __name__, __file__, "/jeux/tresFute")

# Nom du jeu tel qu'enregistré dans la table `jeux` (colonne `name`).
# ⚠️ À ajuster si le nom en base diffère (ex: "Très Futé").
NOM_JEU = "tresFute"


@tresFute_bp.route("/")
@require_permission("showGame")
def page():
    return render_template(tresFute_bp.get_templates_path("tresFute.html"))


@tresFute_bp.route("/game")
@require_permission("showGame")
def tresFute_game():
    return render_template(tresFute_bp.get_templates_path("tresFuteGame.html"))


# ═══════════════════════════════════════════════════════════════
#  API : joueurs (pour le formulaire d'envoi de score)
# ═══════════════════════════════════════════════════════════════

@tresFute_bp.route("/api/joueurs", methods=["GET"])
@require_permission("showGame")
def api_get_joueurs():
    """Retourne la liste des joueurs existants."""
    return jsonify(get_all_joueurs())


@tresFute_bp.route("/api/joueurs", methods=["POST"])
@require_permission("showGame")
def api_create_joueur():
    """Crée un nouveau joueur. Attend { "prenom": str, "nom": str }."""
    data = request.get_json(silent=True) or {}
    prenom = (data.get("prenom") or "").strip()
    nom = (data.get("nom") or "").strip()

    if not prenom or not nom:
        return jsonify({"error": "Le prénom et le nom sont requis."}), 400

    if joueur_exists(prenom, nom):
        return jsonify({"error": "Ce joueur existe déjà."}), 409

    joueur_id = create_joueur(prenom, nom)
    return jsonify({"id": joueur_id, "prenom": prenom, "nom": nom}), 201


# ═══════════════════════════════════════════════════════════════
#  API : parties (pour le formulaire d'envoi de score)
# ═══════════════════════════════════════════════════════════════

@tresFute_bp.route("/api/parties", methods=["GET"])
@require_permission("showGame")
def api_get_parties():
    """Retourne la liste des parties existantes pour ce jeu."""
    return jsonify(get_parties_by_jeu(NOM_JEU))


@tresFute_bp.route("/api/parties", methods=["POST"])
@require_permission("showGame")
def api_create_partie():
    """Crée une nouvelle partie (vide) pour ce jeu."""
    try:
        partie_id = create_partie_simple(NOM_JEU)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"id": partie_id}), 201


# ═══════════════════════════════════════════════════════════════
#  Soumission du score d'un joueur pour une partie
# ═══════════════════════════════════════════════════════════════

@tresFute_bp.route("/submit", methods=["POST"])
@require_permission("showGame")
def tresFute_submit():
    """
    Enregistre le score d'un joueur pour une partie.
    Attend en JSON : { "joueur_id": int, "partie_id": int, "score": int }
    """
    data = request.get_json(silent=True) or {}
    joueur_id = data.get("joueur_id")
    partie_id = data.get("partie_id")
    score = data.get("score")

    if not isinstance(joueur_id, int) or not isinstance(partie_id, int) or not isinstance(score, int):
        return jsonify({"error": "joueur_id, partie_id et score (entiers) sont requis."}), 400

    try:
        submit_score(joueur_id, partie_id, score)
    except Exception as exc:
        return jsonify({"error": f"Échec de l'enregistrement du score : {exc}"}), 500

    return jsonify({"ok": True})