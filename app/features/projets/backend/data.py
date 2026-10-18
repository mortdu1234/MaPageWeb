"""Données des projets affichés sur /projets.

Pour ajouter un projet : ajouter un dictionnaire dans PROJECTS.
- slug      : identifiant dans l'URL (/projets/<slug>), sans espaces ni accents
- type      : "academique" ou "personnel"
- git       : URL du dépôt, ou None
- accroche  : la phrase du CV
- objectif  : liste de paragraphes
- realisation : liste de paragraphes ou de points
- problemes : liste de {"titre", "probleme", "solution"} (peut rester vide)
"""

TYPES = {"academique": "Académique", "personnel": "Personnel"}

PROJECTS = [
    {
        "slug": "homelab",
        "nom": "HomeLab personnel",
        "date": "2025 - 2026",
        "type": "personnel",
        "git": None,
        "court": "Serveur Proxmox auto-hébergé avec accès distant sécurisé et authentification centralisée.",
        "accroche": "Conception d'un serveur sous Proxmox : accès distant sécurisé via WireGuard, reverse proxy Nginx et SSO avec Keycloak pour mes applications conteneurisées.",
        "stack": ["Proxmox", "LXC", "WireGuard", "Nginx", "Keycloak", "Docker"],
        "objectif": [
            "Héberger mes propres services (site web, applications) sur un serveur que je maîtrise de bout en bout, tout en les exposant de façon sécurisée.",
            "Ce projet me sert aussi de terrain d'apprentissage pour l'administration système et la sécurité réseau.",
        ],
        "realisation": [
            "Virtualisation avec Proxmox : services isolés dans des conteneurs LXC et Docker.",
            "Accès distant via un tunnel WireGuard hébergé dans un conteneur LXC.",
            "Reverse proxy Nginx pour exposer les services.",
            "Keycloak comme SSO pour les applications conteneurisées.",
        ],
        "problemes": [],
    },
    {
        "slug": "smile-life",
        "nom": "Smile Life en ligne",
        "date": "2026",
        "type": "personnel",
        "git": None,
        "court": "Version web du jeu de société Smile Life, avec gestion des sessions et validation des entrées.",
        "accroche": "Développement en Python (Flask) d'une version web du jeu de société Smile Life avec une gestion des sessions et une validation des entrées.",
        "stack": ["Python", "Flask", "JavaScript"],
        "objectif": [
            "Proposer une version en ligne de Smile Life jouable entre amis, en soignant la sécurité de l'application.",
        ],
        "realisation": [
            "Application web en Python avec Flask.",
            "Gestion des sessions de jeu.",
            "Validation des entrées côté serveur.",
        ],
        "problemes": [],
    },
    {
        "slug": "site-web",
        "nom": "Site web personnel",
        "date": "2026",
        "type": "personnel",
        "git": None,
        "court": "Mon portfolio, développé en Flask et hébergé dans un conteneur Docker sur mon serveur.",
        "accroche": "Conception de mon site en Python (Flask) hébergé dans un conteneur Docker sur mon serveur.",
        "stack": ["Python", "Flask", "Docker", "JavaScript"],
        "objectif": [
            "Disposer d'une vitrine regroupant mes projets, mon CV et mes outils personnels.",
        ],
        "realisation": [
            "Application Flask organisée en blueprints, un par fonctionnalité.",
            "Déploiement dans un conteneur Docker sur mon HomeLab.",
        ],
        "problemes": [],
    },
    {
        "slug": "chiffrement-rsa-aes",
        "nom": "Chiffrement RSA et AES",
        "date": "2025",
        "type": "academique",
        "git": None,
        "court": "Implémentation complète de RSA et AES en Python et analyse des erreurs d'implémentation.",
        "accroche": "Implémentation complète des algorithmes en Python tout en analysant différentes erreurs d'implémentation (side-channel attacks).",
        "stack": ["Python", "Cryptographie", "Side-channel"],
        "objectif": [
            "Comprendre le fonctionnement interne de RSA et AES en les programmant sans bibliothèque de chiffrement.",
            "Étudier comment une implémentation correcte sur le papier peut fuiter des informations (side-channel attacks).",
        ],
        "realisation": [
            "Implémentation de RSA en Python.",
            "Implémentation d'AES en Python.",
            "Analyse de différentes erreurs d'implémentation exposant à des attaques par canaux auxiliaires.",
        ],
        "problemes": [
            {
                "titre": "[À compléter] Exemple de difficulté",
                "probleme": "Décris l'obstacle rencontré.",
                "solution": "Décris comment tu l'as résolu.",
            }
        ],
    },
    {
        "slug": "algorithme-genetique",
        "nom": "Algorithme génétique",
        "date": "2025",
        "type": "academique",
        "git": None,
        "court": "Génération d'un labyrinthe avec DFS, puis résolution par un algorithme génétique.",
        "accroche": "Réalisation d'un labyrinthe en Python avec l'algorithme DFS puis résolution via un algorithme génétique.",
        "stack": ["Python", "DFS", "Algorithme génétique"],
        "objectif": [
            "Découvrir les algorithmes génétiques en les appliquant à un problème concret : trouver la sortie d'un labyrinthe.",
        ],
        "realisation": [
            "Génération du labyrinthe avec un parcours en profondeur (DFS).",
            "Résolution par un algorithme génétique.",
        ],
        "problemes": [],
    },
    {
        "slug": "etude-siem",
        "nom": "Étude de logiciels SIEM",
        "date": "2024",
        "type": "academique",
        "git": None,
        "court": "Étude comparative de Microsoft Sentinel, IBM QRadar et Splunk.",
        "accroche": "Étude comparative de différents logiciels SIEM (Microsoft Sentinel, IBM QRadar, Splunk).",
        "stack": ["Microsoft Sentinel", "IBM QRadar", "Splunk"],
        "objectif": [
            "Comparer plusieurs solutions SIEM pour comprendre leurs approches de la détection et de la supervision de la sécurité.",
        ],
        "realisation": [
            "Étude comparative de Microsoft Sentinel, IBM QRadar et Splunk.",
        ],
        "problemes": [],
    },
    {
        "slug": "loup-garou",
        "nom": "Jeu du Loup-Garou",
        "date": "2024",
        "type": "academique",
        "git": None,
        "court": "Projet de groupe en Python, mené avec des outils de gestion de projet.",
        "accroche": "Projet de groupe en Python en utilisant des outils de gestion de projet (Git).",
        "stack": ["Python", "Git"],
        "objectif": [
            "Développer un jeu en équipe et apprendre à travailler à plusieurs sur un même code avec Git.",
        ],
        "realisation": [
            "Développement du jeu en Python.",
            "Collaboration avec Git : branches, fusions et gestion des conflits.",
        ],
        "problemes": [],
    },
]


def get_project(slug):
    return next((p for p in PROJECTS if p["slug"] == slug), None)


def all_stacks():
    return sorted({s for p in PROJECTS for s in p["stack"]}, key=str.lower)