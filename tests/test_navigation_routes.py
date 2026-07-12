import re
from pathlib import Path

from app import create_app


ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = ROOT / "app"
PATTERN = re.compile(r"url_for\(\s*['\"]([A-Za-z0-9_.]+)", re.MULTILINE)


def test_all_url_for_references_target_registered_endpoints():
    app = create_app()
    registered_endpoints = set(app.view_functions.keys())
    offenders = []

    for path in APP_ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in {".py", ".html", ".js", ".j2"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for endpoint in PATTERN.findall(text):
            if endpoint == "static" or endpoint.split(".", 1)[0] in {"url_for"}:
                continue
            if endpoint not in registered_endpoints:
                offenders.append(f"{path.relative_to(ROOT)} -> {endpoint}")

    assert not offenders, f"Références d’endpoint invalides détectées : {offenders}"
