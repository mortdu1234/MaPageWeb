"""
pterodactyl_client.py — Client bas niveau pour l'API Pterodactyl (via pydactyl)

Ce module est le SEUL endroit qui parle directement à pydactyl. Toute la logique
métier (formatage, dispatch par type de serveur, etc.) vit ailleurs.
"""

from pydactyl import PterodactylClient
from app.config import Config


_api = PterodactylClient(Config.PANEL_URL, Config.CLIENT_API_KEY)


class PterodactylClientWrapper:
    """Fine couche d'accès brut à l'API Pterodactyl."""

    @staticmethod
    def list_servers() -> list[dict]:
        """Liste brute de tous les serveurs du compte."""
        return _api.client.servers.list_servers().collect()

    @staticmethod
    def get_server(identifier: str) -> dict:
        """Attributs statiques d'un serveur (inclut la relation egg)."""
        return _api.client.servers.get_server(identifier, includes=["egg"])

    @staticmethod
    def get_utilization(identifier: str) -> dict:
        """Métriques live (CPU, RAM, disque, uptime…)."""
        return _api.client.servers.get_server_utilization(identifier)

    @staticmethod
    def list_variables(identifier: str) -> list:
        """Variables d'environnement (startup variables) du serveur."""
        return _api.client.servers.startup.list_variables(identifier).get("data", [])

    @staticmethod
    def list_allocations(identifier: str) -> list:
        return _api.client.servers.network.list_allocations(identifier).get("data", [])

    @staticmethod
    def list_backups(identifier: str) -> list:
        return _api.client.servers.backups.list_backups(identifier).get("data", [])

    @staticmethod
    def create_backup(identifier: str) -> dict:
        return _api.client.servers.backups.create_backup(identifier)

    @staticmethod
    def send_power_action(identifier: str, signal: str) -> None:
        """signal ∈ {'start', 'stop', 'restart', 'kill'}"""
        _api.client.servers.send_power_action(identifier, signal)

    @staticmethod
    def get_websocket_client(identifier: str):
        """Retourne un WebsocketClient pydactyl prêt à être connecté."""
        return _api.client.servers.get_websocket_client(identifier)