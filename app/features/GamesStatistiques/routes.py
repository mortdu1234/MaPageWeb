from flask import render_template, jsonify, abort

from app.core.utils.routesHelper import require_permission
from app.core.utils.blueprints import make_blueprint
from app.core.db.backend.stats import (
    get_all_jeux,
    get_nb_parties_par_jeu,
    get_classement_global,
    get_classement_par_jeu,
    get_extremes_jeu,
    get_parties_detail_par_jeu,
    get_parties_detail_joueur_jeu,
    get_stats_joueur,
)
from app.core.db.backend.joueurs import get_all_joueurs

stats_bp = make_blueprint("statistiques", __name__, __file__, "/statistiques")


@stats_bp.route("/")
@require_permission("showStats")
def page():
    """Page principale des statistiques (bâtie sur base.html)."""
    return render_template(
        stats_bp.get_templates_path("statistiques.html"),
        jeux=get_all_jeux(),
        joueurs=get_all_joueurs(),
    )


# ─── API JSON consommée par stats.js ──────────────────────────────────────────

@stats_bp.route("/api/global")
@require_permission("showStats")
def api_global():
    """Vue d'ensemble : nb de parties par jeu + classement général tous jeux confondus."""
    return jsonify({
        "parties_par_jeu": get_nb_parties_par_jeu(),
        "classement": get_classement_global(),
    })


@stats_bp.route("/api/jeu/<int:jeu_id>")
@require_permission("showStats")
def api_jeu(jeu_id):
    """
    Classement détaillé, extrêmes (score le plus bas / le plus haut)
    et historique complet des parties pour un jeu donné.
    """
    return jsonify({
        "classement": get_classement_par_jeu(jeu_id),
        "extremes": get_extremes_jeu(jeu_id),
        "parties": get_parties_detail_par_jeu(jeu_id),
    })


@stats_bp.route("/api/joueur/<int:joueur_id>")
@require_permission("showStats")
def api_joueur(joueur_id):
    """Statistiques détaillées (par jeu + totaux) pour un joueur donné."""
    data = get_stats_joueur(joueur_id)
    if data is None:
        abort(404)
    return jsonify(data)


@stats_bp.route("/api/joueur/<int:joueur_id>/jeu/<int:jeu_id>")
@require_permission("showStats")
def api_joueur_jeu(joueur_id, jeu_id):
    """
    Historique des parties d'un jeu auxquelles un joueur a participé
    (avec le score de tous les joueurs de chaque partie). Utilisé pour
    dérouler le détail quand on clique sur un jeu dans la fiche joueur.
    """
    return jsonify(get_parties_detail_joueur_jeu(joueur_id, jeu_id))