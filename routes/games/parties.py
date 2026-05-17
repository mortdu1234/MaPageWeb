"""
routes/games/parties.py
Routes de saisie et d'enregistrement des parties pour chaque jeu.

Chaque jeu expose trois URL :
  GET  /<jeu>/partie/nouvelle   → formulaire de saisie
  POST /<jeu>/partie/submit     → traitement et insertion en BDD
  GET  /<jeu>/parties           → historique des parties

Toutes les routes nécessitent la permission "showGame".
"""

from flask import render_template, request, redirect, url_for, flash, abort
from routes import require_permission
from routes.games import jeux_bp
from db.joueurs import get_all_joueurs
from db.parties import (
    get_parties_by_jeu,
    create_partie_ohanami,
    create_partie_qwirkle,
    create_partie_smilelife,
    create_partie_train_mexicain,
    create_partie_tres_fute,
    create_partie_triomino,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _joueur_ids_from_form() -> list[int]:
    """Récupère la liste ordonnée des joueur_id cochés dans le formulaire."""
    return [int(jid) for jid in request.form.getlist("joueur_id") if jid.isdigit()]


def _date_from_form() -> str | None:
    d = request.form.get("date_partie", "").strip()
    return d or None


def _notes_from_form() -> str | None:
    n = request.form.get("notes", "").strip()
    return n or None


def _score_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


# ─── Ohanami ──────────────────────────────────────────────────────────────────

@jeux_bp.route("/oanami/partie/nouvelle")
@require_permission("showGame")
def oanami_nouvelle_partie():
    joueurs = get_all_joueurs()
    return render_template("jeux/parties/oanami_form.html", joueurs=joueurs)


@jeux_bp.route("/oanami/partie/submit", methods=["POST"])
@require_permission("showGame")
def oanami_partie_submit():
    joueur_ids = _joueur_ids_from_form()
    if len(joueur_ids) < 2:
        flash("Sélectionnez au moins 2 joueurs.", "error")
        return redirect(url_for("jeux.oanami_nouvelle_partie"))

    scores = []
    for jid in joueur_ids:
        scores.append({
            "joueur_id":   jid,
            "score_rouge": _score_int(request.form.get(f"rouge_{jid}")),
            "score_bleu":  _score_int(request.form.get(f"bleu_{jid}")),
            "score_vert":  _score_int(request.form.get(f"vert_{jid}")),
        })

    try:
        create_partie_ohanami(scores, date_partie=_date_from_form(), notes=_notes_from_form())
        flash("Partie Ohanami enregistrée !", "success")
    except Exception as e:
        flash(f"Erreur lors de l'enregistrement : {e}", "error")

    return redirect(url_for("jeux.oanami_parties"))


@jeux_bp.route("/oanami/parties")
@require_permission("showGame")
def oanami_parties():
    parties = get_parties_by_jeu("ohanami")
    return render_template("jeux/parties/historique.html",
                           jeu="Ohanami", parties=parties,
                           url_nouvelle=url_for("jeux.oanami_nouvelle_partie"))


# ─── Qwirkle ──────────────────────────────────────────────────────────────────

@jeux_bp.route("/qwirkle/partie/nouvelle")
@require_permission("showGame")
def qwirkle_nouvelle_partie():
    joueurs = get_all_joueurs()
    return render_template("jeux/parties/qwirkle_form.html", joueurs=joueurs)


@jeux_bp.route("/qwirkle/partie/submit", methods=["POST"])
@require_permission("showGame")
def qwirkle_partie_submit():
    joueur_ids = _joueur_ids_from_form()
    if len(joueur_ids) < 2:
        flash("Sélectionnez au moins 2 joueurs.", "error")
        return redirect(url_for("jeux.qwirkle_nouvelle_partie"))

    scores = []
    for jid in joueur_ids:
        scores.append({
            "joueur_id":         jid,
            "score":             _score_int(request.form.get(f"score_{jid}")),
            "qwirkles_realises": _score_int(request.form.get(f"qwirkles_{jid}")),
        })

    try:
        create_partie_qwirkle(scores, date_partie=_date_from_form(), notes=_notes_from_form())
        flash("Partie Qwirkle enregistrée !", "success")
    except Exception as e:
        flash(f"Erreur lors de l'enregistrement : {e}", "error")

    return redirect(url_for("jeux.qwirkle_parties"))


@jeux_bp.route("/qwirkle/parties")
@require_permission("showGame")
def qwirkle_parties():
    parties = get_parties_by_jeu("qwirkle")
    return render_template("jeux/parties/historique.html",
                           jeu="Qwirkle", parties=parties,
                           url_nouvelle=url_for("jeux.qwirkle_nouvelle_partie"))


# ─── SmileLife ────────────────────────────────────────────────────────────────

@jeux_bp.route("/smileLife/partie/nouvelle")
@require_permission("showGame")
def smilelife_nouvelle_partie():
    joueurs = get_all_joueurs()
    return render_template("jeux/parties/simple_form.html",
                           jeu="SmileLife", joueurs=joueurs,
                           url_submit=url_for("jeux.smilelife_partie_submit"))


@jeux_bp.route("/smileLife/partie/submit", methods=["POST"])
@require_permission("showGame")
def smilelife_partie_submit():
    joueur_ids = _joueur_ids_from_form()
    if len(joueur_ids) < 2:
        flash("Sélectionnez au moins 2 joueurs.", "error")
        return redirect(url_for("jeux.smilelife_nouvelle_partie"))

    scores = [{"joueur_id": jid,
               "score": _score_int(request.form.get(f"score_{jid}"))}
              for jid in joueur_ids]

    try:
        create_partie_smilelife(scores, date_partie=_date_from_form(), notes=_notes_from_form())
        flash("Partie SmileLife enregistrée !", "success")
    except Exception as e:
        flash(f"Erreur lors de l'enregistrement : {e}", "error")

    return redirect(url_for("jeux.smilelife_parties"))


@jeux_bp.route("/smileLife/parties")
@require_permission("showGame")
def smilelife_parties():
    parties = get_parties_by_jeu("smilelife")
    return render_template("jeux/parties/historique.html",
                           jeu="SmileLife", parties=parties,
                           url_nouvelle=url_for("jeux.smilelife_nouvelle_partie"))


# ─── Train Mexicain ───────────────────────────────────────────────────────────

@jeux_bp.route("/trainMexicain/partie/nouvelle")
@require_permission("showGame")
def train_mexicain_nouvelle_partie():
    joueurs = get_all_joueurs()
    return render_template("jeux/parties/penalite_form.html",
                           jeu="Train Mexicain", joueurs=joueurs,
                           url_submit=url_for("jeux.train_mexicain_partie_submit"),
                           label_penalite="Points de dominos non posés",
                           plus_petit_gagne=True)


@jeux_bp.route("/trainMexicain/partie/submit", methods=["POST"])
@require_permission("showGame")
def train_mexicain_partie_submit():
    joueur_ids = _joueur_ids_from_form()
    if len(joueur_ids) < 2:
        flash("Sélectionnez au moins 2 joueurs.", "error")
        return redirect(url_for("jeux.train_mexicain_nouvelle_partie"))

    scores = [{"joueur_id": jid,
               "score":     _score_int(request.form.get(f"score_{jid}")),
               "penalites": _score_int(request.form.get(f"penalites_{jid}"))}
              for jid in joueur_ids]

    try:
        create_partie_train_mexicain(scores, date_partie=_date_from_form(), notes=_notes_from_form())
        flash("Partie Train Mexicain enregistrée !", "success")
    except Exception as e:
        flash(f"Erreur lors de l'enregistrement : {e}", "error")

    return redirect(url_for("jeux.train_mexicain_parties"))


@jeux_bp.route("/trainMexicain/parties")
@require_permission("showGame")
def train_mexicain_parties():
    parties = get_parties_by_jeu("trainmexicain")
    return render_template("jeux/parties/historique.html",
                           jeu="Train Mexicain", parties=parties,
                           url_nouvelle=url_for("jeux.train_mexicain_nouvelle_partie"))


# ─── Très Futé ────────────────────────────────────────────────────────────────

@jeux_bp.route("/tresFute/partie/nouvelle")
@require_permission("showGame")
def tres_fute_nouvelle_partie():
    joueurs = get_all_joueurs()
    return render_template("jeux/parties/simple_form.html",
                           jeu="Très Futé", joueurs=joueurs,
                           url_submit=url_for("jeux.tres_fute_partie_submit"))


@jeux_bp.route("/tresFute/partie/submit", methods=["POST"])
@require_permission("showGame")
def tres_fute_partie_submit():
    joueur_ids = _joueur_ids_from_form()
    if len(joueur_ids) < 2:
        flash("Sélectionnez au moins 2 joueurs.", "error")
        return redirect(url_for("jeux.tres_fute_nouvelle_partie"))

    scores = [{"joueur_id": jid,
               "score": _score_int(request.form.get(f"score_{jid}"))}
              for jid in joueur_ids]

    try:
        create_partie_tres_fute(scores, date_partie=_date_from_form(), notes=_notes_from_form())
        flash("Partie Très Futé enregistrée !", "success")
    except Exception as e:
        flash(f"Erreur lors de l'enregistrement : {e}", "error")

    return redirect(url_for("jeux.tres_fute_parties"))


@jeux_bp.route("/tresFute/parties")
@require_permission("showGame")
def tres_fute_parties():
    parties = get_parties_by_jeu("tresfute")
    return render_template("jeux/parties/historique.html",
                           jeu="Très Futé", parties=parties,
                           url_nouvelle=url_for("jeux.tres_fute_nouvelle_partie"))


# ─── Triomino ─────────────────────────────────────────────────────────────────

@jeux_bp.route("/triomino/partie/nouvelle")
@require_permission("showGame")
def triomino_nouvelle_partie():
    joueurs = get_all_joueurs()
    return render_template("jeux/parties/penalite_form.html",
                           jeu="Triomino", joueurs=joueurs,
                           url_submit=url_for("jeux.triomino_partie_submit"),
                           label_penalite="Pièces non jouées",
                           plus_petit_gagne=True)


@jeux_bp.route("/triomino/partie/submit", methods=["POST"])
@require_permission("showGame")
def triomino_partie_submit():
    joueur_ids = _joueur_ids_from_form()
    if len(joueur_ids) < 2:
        flash("Sélectionnez au moins 2 joueurs.", "error")
        return redirect(url_for("jeux.triomino_nouvelle_partie"))

    scores = [{"joueur_id": jid,
               "score":     _score_int(request.form.get(f"score_{jid}")),
               "penalites": _score_int(request.form.get(f"penalites_{jid}"))}
              for jid in joueur_ids]

    try:
        create_partie_triomino(scores, date_partie=_date_from_form(), notes=_notes_from_form())
        flash("Partie Triomino enregistrée !", "success")
    except Exception as e:
        flash(f"Erreur lors de l'enregistrement : {e}", "error")

    return redirect(url_for("jeux.triomino_parties"))


@jeux_bp.route("/triomino/parties")
@require_permission("showGame")
def triomino_parties():
    parties = get_parties_by_jeu("triomino")
    return render_template("jeux/parties/historique.html",
                           jeu="Triomino", parties=parties,
                           url_nouvelle=url_for("jeux.triomino_nouvelle_partie"))