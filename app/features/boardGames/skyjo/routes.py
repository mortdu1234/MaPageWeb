from flask import render_template, request, redirect, url_for, flash
from app.core.utils.routesHelper import require_permission, validate_json
from app.core.db.backend.parties import create_partie
from app.core.utils.blueprints import make_blueprint

skyjo_bp = make_blueprint("skyjo", __name__, __file__, "/jeux/skyjo")

def _int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default




@skyjo_bp.route("/")
@require_permission("showGame")
def page():
    return render_template(skyjo_bp.get_templates_path("skyjo.html"))


@skyjo_bp.route("/game")
@require_permission("showGame")
def skyjo_game():
    return render_template(skyjo_bp.get_templates_path("skyjoGame.html"))


@skyjo_bp.route("/submit", methods=["POST"])
@require_permission("showGame")
@validate_json("skyjo.json")
def skyjo_submit():
    data = request.get_json()
    
    # DEBUG
    print(f"DEBUG - Données reçues : {data}")
    
    nb_joueurs = _int(data.get("nb_joueurs"), 0)
    joueurs = data.get("joueurs", [])
    
    print(f"DEBUG - nb_joueurs: {nb_joueurs}, nb joueurs dans array: {len(joueurs)}")
    
    # Construire le dictionnaire de scores : {id_joueur: score}
    scores = {}
    for joueur in joueurs:
        joueur_id = _int(joueur.get("id"))
        score = _int(joueur.get("score"), 0)
        
        print(f"DEBUG - Joueur ID: {joueur_id}, Score: {score}")
        
        if joueur_id is not None:
            scores[joueur_id] = score
    
    print(f"DEBUG - Scores finaux: {scores}")
    
    # Créer la partie avec les scores
    try:
        payload = {
            "jeu": "skyjo",
            "nb_joueurs": nb_joueurs,
            "scores": scores
        }
        print(f"DEBUG - Payload envoyé à create_partie: {payload}")
        
        partie_id = create_partie(payload)
        print(f"DEBUG - Partie créée avec succès, ID: {partie_id}")
        
        flash(f"✓ Partie Skyjo créée avec succès (ID: {partie_id})", "success")
    except Exception as e:
        print(f"DEBUG - Erreur lors de create_partie: {str(e)}")
        flash(f"✗ Erreur lors de la création de la partie : {str(e)}", "error")
        return redirect(url_for("skyjo.skyjo_game"))
    
    return redirect(url_for("skyjo.skyjo_game"))