from flask import render_template, abort
from app.core.utils.blueprints import make_blueprint
from .backend.data import PROJECTS, TYPES, get_project, all_stacks

projets_bp = make_blueprint("projets", __name__, __file__, url_prefix="/projets")


def _render(name, **ctx):
    # tpl() permet aux templates d'inclure d'autres templates du blueprint
    return render_template(
        projets_bp.get_templates_path(name),
        tpl=projets_bp.get_templates_path,
        types=TYPES,
        **ctx,
    )


@projets_bp.route("/")
def mesprojets():
    sections = [
        {"key": key, "titre": label, "projets": [p for p in PROJECTS if p["type"] == key]}
        for key, label in TYPES.items()
    ]
    return _render("hub.html", sections=sections, stacks=all_stacks())


@projets_bp.route("/<slug>")
def projet(slug):
    project = get_project(slug)
    if project is None:
        abort(404)
    return _render("projects/main.html", project=project)