from flask import render_template, request, redirect, url_for, flash
from app.core.utils.routesHelper import require_permission, validate_json
from app.core.db.backend.parties import create_partie
from app.core.utils.blueprints import make_blueprint

ohanami_bp = make_blueprint("ohanami", __name__, __file__, "/jeux/ohanami")

def _int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default




@ohanami_bp.route("/")
@require_permission("showGame")
def page():
    return render_template(ohanami_bp.get_templates_path("oanami.html"))


@ohanami_bp.route("/game")
@require_permission("showGame")
def oanami_game():
    return render_template(ohanami_bp.get_templates_path("oanamiGame.html"))


@ohanami_bp.route("/submit", methods=["POST"])
@require_permission("showGame")
@validate_json("ohanami.json")
def oanami_submit():
    data = request.get_json()
    joueurs = data.get("joueurs", [])

    sakura_tab = [0, 1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66, 78, 91, 105, 120]

    # Calcul des scores totaux
    scores = {}
    for joueur in joueurs:
        score = 0
        for value in data.get("scores", []):
            player_score = value.get("joueurs", {}).get(f"joueur{joueur.get('joueur', 0)}", 0)
            match value.get("type"):
                case "eau":
                    score += player_score * 3
                case "herbe":
                    score += player_score * 4
                case "pierre":
                    score += player_score * 7
                case "sakura":
                    score += sakura_tab[_int(player_score)]

        scores[joueur.get("id")] = score

    data_send = {
        "jeu": "ohanami",
        "nb_joueurs": len(joueurs),
        "scores": scores
    }

    create_partie(data_send)
    flash("Partie enregistrée avec succès !", "success")

    return redirect(url_for("jeux.oanami_game"))