from flask import render_template
from app.core.utils.blueprints import make_blueprint
from app.features.projets.helpers import load_header

homelab_bp = make_blueprint("projet_homelab", __name__, __file__, url_prefix="/homelab")

# ── Un blueprint par service du HomeLab (même structure que les autres projets) ──
from .databases.routes import databases_bp
from .reverseProxy.routes import reverse_proxy_bp
from .cloudPerso.routes import cloud_bp
from .vpnWireguard.routes import vpn_bp
from .serveurGaming.routes import gaming_bp
from .sso.routes import sso_bp
from .hedgedoc.routes import hedgedoc_bp
from .wikijs.routes import wikijs_bp

# Ordre d'affichage dans la liste des services.
SERVICE_BLUEPRINTS = [
    databases_bp,
    reverse_proxy_bp,
    cloud_bp,
    vpn_bp,
    gaming_bp,
    sso_bp,
    hedgedoc_bp,
    wikijs_bp,
]

for _bp in SERVICE_BLUEPRINTS:
    homelab_bp.register_blueprint(_bp)


@homelab_bp.route("/")
def index():
    # header.json est relu à chaque requête.
    services = [load_header(bp, endpoint_prefix=f"projets.{homelab_bp.name}") for bp in SERVICE_BLUEPRINTS]
    return render_template(
        homelab_bp.get_templates_path("projet_homelab.html"),
        project=load_header(homelab_bp),
        services=services,
    )
