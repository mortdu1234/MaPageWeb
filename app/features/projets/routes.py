from flask import render_template
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

projets_bp = make_blueprint("projets", __name__, __file__, url_prefix="/projets")

# ── Un blueprint par projet : chaque dossier contient routes.py, templates/ et static/ ──
from .homelab.routes import homelab_bp
from .smileLife.routes import smile_life_bp
from .siteWeb.routes import site_web_bp
from .rsaAes.routes import rsa_aes_bp
from .algoGenetique.routes import algo_genetique_bp
from .etudeSiem.routes import etude_siem_bp
from .loupGarou.routes import loup_garou_bp

# Ordre d'affichage dans le hub. Pour ajouter un projet : importer son blueprint et l'ajouter ici.
PROJECT_BLUEPRINTS = [
    homelab_bp,
    smile_life_bp,
    site_web_bp,
    rsa_aes_bp,
    algo_genetique_bp,
    etude_siem_bp,
    loup_garou_bp,
]

for _bp in PROJECT_BLUEPRINTS:
    projets_bp.register_blueprint(_bp)

TYPES = {"academique": "Académique", "personnel": "Personnel"}


@projets_bp.context_processor
def inject_tpl():
    # tpl("projects/header.html") donne le bon chemin de template, comme get_templates_path.
    # Disponible aussi dans les pages des projets (blueprints enfants).
    return {"tpl": projets_bp.get_templates_path}


@projets_bp.route("/")
def mesprojets():
    # header.json est relu à chaque requête : pas besoin de redémarrer après une modification.
    projects = [load_header(bp) for bp in PROJECT_BLUEPRINTS]
    sections = [
        {"key": key, "titre": label, "projets": [p for p in projects if p["type"] == key]}
        for key, label in TYPES.items()
    ]
    stacks = sorted({s for p in projects for s in p["stack"]}, key=str.lower)
    return render_template(
        projets_bp.get_templates_path("hub.html"),
        sections=sections,
        stacks=stacks,
        types=TYPES,
    )
