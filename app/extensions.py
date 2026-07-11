"""
Instances des extensions, séparées de l'app factory pour éviter les
imports circulaires (chaque module peut faire `from app.extensions import db`
sans jamais importer `app/__init__.py`).
"""
