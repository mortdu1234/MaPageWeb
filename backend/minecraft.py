"""
minecraft.py — Couche service Pterodactyl via pydactyl
pip install py-dactyl flask-sock
"""

from pydactyl import PterodactylClient
from config import Config


api = PterodactylClient(Config.PANEL_URL, Config.CLIENT_API_KEY)


# ══════════════════════════════════════════════════════════════
#  COUCHE BASSE — appels directs à pydactyl
# ══════════════════════════════════════════════════════════════

class PterodactyleAPI:

    @staticmethod
    def get_client_infos():
        """Retourne la liste brute de tous les serveurs du compte."""
        return api.client.servers.list_servers().collect()

    @staticmethod
    def get_server_detail(identifier: str) -> dict:
        """Retourne les attributs statiques d'un serveur.
        Inclut les relations egg et variables d'environnement.
        """
        return api.client.servers.get_server(identifier, includes=["egg"]) # pyright: ignore[reportReturnType]

    @staticmethod
    def get_server_infos(identifier: str) -> dict:
        """Retourne les métriques live (CPU, RAM, disque, uptime…)."""
        return api.client.servers.get_server_utilization(identifier)  # pyright: ignore[reportReturnType]
    
    @staticmethod
    def get_env_vars(identifier: str) -> list:
        response = api.client.servers.startup.list_variables(identifier)
        return response.get("data", [])

    @staticmethod
    def get_allocations(identifier: str) -> list:
        response = api.client.servers.network.list_allocations(identifier)
        return response.get("data", [])

    @staticmethod
    def get_backups(identifier: str) -> list:
        response = api.client.servers.backups.list_backups(identifier)
        return response.get("data", [])
    
    @staticmethod
    def create_backup(identifier: str) -> dict:
        """Lance la création d'une sauvegarde, retourne ses attributs."""
        return api.client.servers.backups.create_backup(identifier) # pyright: ignore[reportReturnType]

    @staticmethod
    def power_server(identifier: str, signal: str):
        """Envoie un signal de contrôle au serveur (start/stop/restart/kill)."""
        api.client.servers.send_power_action(identifier, signal)

    @staticmethod
    def get_websocket_client(identifier: str):
        """Retourne un WebsocketClient pydactyl prêt à être connecté."""
        return api.client.servers.get_websocket_client(identifier)


# ══════════════════════════════════════════════════════════════
#  COUCHE HAUTE — formatage pour le frontend
# ══════════════════════════════════════════════════════════════

class API:

    # ──────────────────────────────────────────────
    #  Liste de tous les serveurs (page d'accueil)
    # ──────────────────────────────────────────────
    @staticmethod
    def get_servers() -> list[dict]:
        """Retourne tous les serveurs avec leurs métriques live.

        Format de chaque élément :
        {
            "id"        : str   — identifiant abrégé (ex: "a1b2c3d4")
            "name"      : str
            "ramLimit"  : int   — en MB
            "diskLimit" : int   — en MB
            "status"    : str   — "running" | "stopped" | "starting" | "stopping"
            "cpuUsed"   : float — en %
            "ramUsed"   : float — en MB
            "diskUsed"  : float — en MB
        }
        """
        result = []
        data_list = PterodactyleAPI.get_client_infos()

        for data_dict in data_list:
            attrs   = data_dict.get("attributes", {})
            limits  = attrs.get("limits", {})
            srv_id  = attrs.get("identifier")

            live_status = "offline"
            cpu_used = ram_used = disk_used = 0

            try:
                stats_live = PterodactyleAPI.get_server_infos(srv_id)
                live_status = stats_live.get("current_state", "offline")
                resources   = stats_live.get("resources", {})
                cpu_used    = resources.get("cpu_absolute", 0)
                ram_used    = resources.get("memory_bytes", 0) / 1_048_576
                disk_used   = resources.get("disk_bytes",   0) / 1_048_576
            except Exception as e:
                print(f"[API.get_servers] Stats indisponibles pour {srv_id}: {e}")

            result.append({
                "id":        srv_id,
                "name":      attrs.get("name"),
                "ramLimit":  limits.get("memory"),
                "diskLimit": limits.get("disk"),
                "status":    live_status,
                "cpuUsed":   round(cpu_used,  2),
                "ramUsed":   round(ram_used,  2),
                "diskUsed":  round(disk_used, 2),
            })

        return result

    # ──────────────────────────────────────────────
    #  Détails statiques d'un serveur
    # ──────────────────────────────────────────────
    @staticmethod
    def get_server_info(identifier: str) -> dict:
        """Retourne les informations statiques formatées d'un serveur.

        Format retourné :
        {
            "id"         : str
            "uuid"       : str
            "name"       : str
            "description": str | None
            "node"       : str | None   — non disponible via l'API client (None)
            "sftp_host"  : str
            "sftp_port"  : int
            "status"     : str
            "egg"        : { "name": str | None, "docker_image": str | None }
            "environment": { "VAR": "value", … }
            "limits"     : { "cpu": int, "memory": int, "disk": int,
                             "swap": int, "io": int }
        }
        """
        raw    = PterodactyleAPI.get_server_detail(identifier)
        attrs  = raw if isinstance(raw, dict) and "identifier" in raw else raw.get("attributes", raw)
        limits = attrs.get("limits", {})

        # Infos SFTP
        sftp   = attrs.get("sftp_details", {})

        # Egg — disponible si pydactyl a inclus la relation "egg"
        relationships = attrs.get("relationships", {})
        egg_attrs     = relationships.get("egg", {}).get("attributes", {})

        # Variables d'environnement
        env_raw = PterodactyleAPI.get_env_vars(identifier)
        environment = {
            item["attributes"]["env_variable"]: item["attributes"]["server_value"]
            for item in env_raw
            if "attributes" in item
        }

        # Statut live
        try:
            stats  = PterodactyleAPI.get_server_infos(identifier)
            status = stats.get("current_state", "stopped")
        except Exception:
            status = "stopped"

        return {
            "id":          attrs.get("identifier"),
            "uuid":        attrs.get("uuid"),
            "name":        attrs.get("name"),
            "description": attrs.get("description") or None,
            "node":        None,   # Nécessite l'API admin pour l'obtenir
            "sftp_host":   sftp.get("ip"),
            "sftp_port":   sftp.get("port"),
            "status":      status,
            "egg": {
                "name":         egg_attrs.get("name"),
                "docker_image": egg_attrs.get("docker_image"),
            },
            "environment": environment,
            "limits": {
                "cpu":    limits.get("cpu",    0),
                "memory": limits.get("memory", 0),
                "disk":   limits.get("disk",   0),
                "swap":   limits.get("swap",   0),
                "io":     limits.get("io",     0),
            },
        }

    # ──────────────────────────────────────────────
    #  Métriques live
    # ──────────────────────────────────────────────
    @staticmethod
    def get_server_resources(identifier: str) -> dict:
        """Retourne les métriques live formatées.

        Format retourné :
        {
            "cpu_percent"         : float   — en %
            "memory_bytes"        : int
            "memory_limit_bytes"  : int
            "disk_bytes"          : int
            "disk_limit_bytes"    : int
            "uptime_seconds"      : int
            "network_rx_bytes"    : int
            "network_tx_bytes"    : int
        }
        """
        raw       = PterodactyleAPI.get_server_infos(identifier)
        resources = raw.get("resources", {})

        # Limites en bytes (stockées en MB dans l'API Pterodactyl)
        # On récupère les limites depuis les attributs du serveur
        try:
            srv_attrs     = PterodactyleAPI.get_server_detail(identifier)
            attrs         = srv_attrs if "limits" in srv_attrs else srv_attrs.get("attributes", {})
            limits        = attrs.get("limits", {})
            mem_limit_mb  = limits.get("memory", 0)
            disk_limit_mb = limits.get("disk",   0)
        except Exception:
            mem_limit_mb = disk_limit_mb = 0

        network = resources.get("network", {})

        return {
            "cpu_percent":        round(resources.get("cpu_absolute", 0), 2),
            "memory_bytes":       resources.get("memory_bytes", 0),
            "memory_limit_bytes": mem_limit_mb  * 1_048_576,
            "disk_bytes":         resources.get("disk_bytes",   0),
            "disk_limit_bytes":   disk_limit_mb * 1_048_576,
            "uptime_seconds":     resources.get("uptime", 0) // 1000,  # ms → s
            "network_rx_bytes":   network.get("rx_bytes", 0),
            "network_tx_bytes":   network.get("tx_bytes", 0),
        }

    # ──────────────────────────────────────────────
    #  Allocations réseau
    # ──────────────────────────────────────────────
    @staticmethod
    def get_server_allocations(identifier: str) -> list[dict]:
        """Retourne la liste des allocations réseau formatées.

        Format de chaque élément :
        {
            "id"         : int
            "ip"         : str
            "port"       : int
            "alias"      : str | None
            "is_default" : bool
        }
        """
        raw = PterodactyleAPI.get_allocations(identifier)
        result = []
        for item in raw:
            a = item.get("attributes", {})
            result.append({
                "id":         a.get("id"),
                "ip":         a.get("ip"),
                "port":       a.get("port"),
                "alias":      a.get("alias") or None,
                "is_default": a.get("is_default", False),
            })
        return result

    # ──────────────────────────────────────────────
    #  Sauvegardes
    # ──────────────────────────────────────────────
    @staticmethod
    def get_server_backups(identifier: str) -> list[dict]:
        """Retourne la liste des sauvegardes formatées.

        Format de chaque élément :
        {
            "uuid"          : str
            "name"          : str
            "size_bytes"    : int
            "created_at"    : str   — ISO 8601
            "is_successful" : bool
        }
        """
        raw = PterodactyleAPI.get_backups(identifier)
        result = []
        for item in raw:
            b = item.get("attributes", {})
            result.append({
                "uuid":          b.get("uuid"),
                "name":          b.get("name"),
                "size_bytes":    b.get("bytes",        0),
                "created_at":    b.get("created_at"),
                "is_successful": b.get("is_successful", False),
            })
        # Plus récentes en premier
        result.sort(key=lambda x: x["created_at"] or "", reverse=True)
        return result

    @staticmethod
    def create_backup(identifier: str) -> dict:
        """Crée une sauvegarde et retourne ses attributs formatés."""
        raw = PterodactyleAPI.create_backup(identifier)
        b   = raw.get("attributes", raw) if isinstance(raw, dict) else {}
        return {
            "uuid":          b.get("uuid"),
            "name":          b.get("name"),
            "size_bytes":    b.get("bytes",        0),
            "created_at":    b.get("created_at"),
            "is_successful": b.get("is_successful", False),
        }

    # ──────────────────────────────────────────────
    #  Contrôle alimentation
    # ──────────────────────────────────────────────
    @staticmethod
    def start_server(identifier: str):
        PterodactyleAPI.power_server(identifier, "start")

    @staticmethod
    def stop_server(identifier: str):
        PterodactyleAPI.power_server(identifier, "stop")

    @staticmethod
    def restart_server(identifier: str):
        PterodactyleAPI.power_server(identifier, "restart")

    @staticmethod
    def kill_server(identifier: str):
        PterodactyleAPI.power_server(identifier, "kill")
    
    @staticmethod
    def power_server(identifier, signal):
        PterodactyleAPI.power_server(identifier, signal)
    

    @staticmethod
    def get_server_all_info(identifier: str):
        return PterodactyleAPI.get_server_infos(identifier)

    # ──────────────────────────────────────────────
    #  WebSocket console
    # ──────────────────────────────────────────────
    @staticmethod
    def get_websocket_client(identifier: str):
        """Retourne un WebsocketClient pydactyl (non connecté)."""
        return PterodactyleAPI.get_websocket_client(identifier)