"""Service distant de minijeux du package app."""

import json
import shlex

import paramiko

from app.config import (
    MINIGAME_VM_HOST,
    MINIGAME_VM_JSON_PATH,
    MINIGAME_VM_PORT,
    MINIGAME_VM_SCRIPT_PATH,
    MINIGAME_VM_SSH_KEY_PATH,
    MINIGAME_VM_USER,
)


class RemoteMinigameServiceError(Exception):
    pass


class RemoteMinigameService:
    def __init__(self):
        self.host = MINIGAME_VM_HOST
        self.port = int(MINIGAME_VM_PORT or 22)
        self.user = MINIGAME_VM_USER
        self.key_path = MINIGAME_VM_SSH_KEY_PATH
        self.script_path = MINIGAME_VM_SCRIPT_PATH
        self.json_path = MINIGAME_VM_JSON_PATH

    def _connect(self) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=self.host,
                port=self.port,
                username=self.user,
                key_filename=self.key_path,
                timeout=10,
            )
        except Exception as exc:  # noqa: BLE001
            raise RemoteMinigameServiceError(f"Connexion SSH impossible vers {self.host}:{self.port} — {exc}") from exc
        return client

    def list_minigames(self) -> list[dict]:
        client = self._connect()
        try:
            sftp = client.open_sftp()
            try:
                with sftp.open(self.json_path, "r") as remote_file:
                    raw = remote_file.read()
            finally:
                sftp.close()
        except FileNotFoundError as exc:
            raise RemoteMinigameServiceError(f"Minigames.json introuvable sur la VM ({self.json_path})") from exc
        finally:
            client.close()

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RemoteMinigameServiceError("Minigames.json distant invalide") from exc

    def switch_game_stream(self, game_name: str):
        client = self._connect()
        try:
            command = f"sudo {shlex.quote(self.script_path)} {shlex.quote(game_name)}"
            stdin, stdout, _stderr = client.exec_command(command, get_pty=True)
            stdin.close()

            channel = stdout.channel
            while True:
                if channel.recv_ready():
                    chunk = channel.recv(4096).decode("utf-8", errors="replace")
                    if chunk:
                        yield chunk
                elif channel.exit_status_ready():
                    break

            exit_status = channel.recv_exit_status()
            if exit_status != 0:
                raise RemoteMinigameServiceError(f"Le script a échoué (code de sortie {exit_status})")
        finally:
            client.close()


__all__ = ["RemoteMinigameService", "RemoteMinigameServiceError"]
