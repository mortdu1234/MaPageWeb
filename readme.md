app/
├── __init__.py              # application factory (create_app)
├── extensions.py            # instances partagées (db, login_manager, etc.)
├── config.py
│
├── core/                    # ce qui est transverse à toute l'app
│   ├── auth/
│   │   ├── routes.py        # ex-routes/auth.py
│   │   ├── services.py      # ex-backend/Auth.py
│   │   └── session.py       # ex-sessionUser.py
│   ├── crypto.py            # ex-backend/crypto.py
│   ├── errors/
│   │   └── routes.py        # ex-routes/errors.py
│   └── db/
│       ├── connection.py    # ex-db/database.py
│       └── users.py         # ex-db/users.py (transverse: users = core)
│
├── features/                # une feature = un dossier autonome
│   ├── games/
│   │   ├── routes/
│   │   │   ├── qwirkle.py
│   │   │   ├── oanami.py
│   │   │   ├── ptit_bac.py
│   │   │   ├── train_mexicain.py
│   │   │   ├── tres_fute.py
│   │   │   ├── triomino.py
│   │   │   └── minijeux.py  # ex-serverMinijeux.py
│   │   ├── services/
│   │   │   └── remote_minigame.py  # ex-backend/RemoteMinigameService.py
│   │   └── db.py            # ex-db/joueurs.py, parties.py
│   │
│   ├── servers/              # regroupe TOUT ce qui touche à l'infra serveurs
│   │   ├── routes.py         # ex-routes/proxmox.py, serverHub.py
│   │   ├── proxmox_client.py # ex-backend/proxmox.py
│   │   ├── pterodactyl_client.py  # ex-pterodactyl/
│   │   └── models/           # ex-ServersGestions/modeles/
│   │       ├── generic_server.py
│   │       ├── minecraft_server.py
│   │       ├── palworld_server.py
│   │       └── server_factory.py
│   │
│   ├── files/
│   │   ├── routes.py         # ex-routes/files.py
│   │   ├── service.py        # ex-backend/FilesService.py
│   │   └── db.py             # ex-db/files.py
│   │
│   ├── tasks/
│   │   ├── routes.py         # ex-routes/tasks.py
│   │   └── db.py             # ex-db/tasks.py, permissions.py
│   │
│   ├── projets/
│   │   └── routes.py         # ex-routes/projets.py
│   │
│   ├── contact/
│   │   ├── routes.py
│   │   ├── service.py        # ex-backend/contact.py
│   │   └── notifications.py  # ex-backend/notifications.py
│   │
│   └── database_viewer/      # ex-routes/database.py (page d'admin BDD)
│       └── routes.py
│
├── rsa_keys.py                # ex-routes/rsaKeys.py (utilitaire, → core/ ou garder isolé)
│
├── static/                     # inchangé
└── templates/                  # inchangé, éventuellement refléter la même
                                 # arborescence (templates/games/, templates/servers/...)

run.py                          # point d'entrée, remplace app.py