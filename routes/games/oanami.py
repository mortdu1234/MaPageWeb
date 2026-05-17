from flask import render_template, request, redirect, url_for, flash
from routes import require_permission, validate_json
from routes.games import jeux_bp
from db.parties import create_partie


def _int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


@jeux_bp.route("/oanami")
@require_permission("showGame")
def oanami():
    return render_template("jeux/oanami.html")


@jeux_bp.route("/oanami/game")
@require_permission("showGame")
def oanami_game():
    return render_template("jeux/oanamiGame.html")


@jeux_bp.route("/oanami/submit", methods=["POST"])
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