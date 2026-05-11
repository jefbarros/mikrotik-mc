from __future__ import annotations

import socket

import paramiko

from .commands import validate_command
from .exceptions import SSHConnectionError
from .safety import validate_provisioning_command


class RouterOSSSHClient:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        timeout: int = 15,
        strict_host_key_checking: bool = False,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.strict_host_key_checking = strict_host_key_checking
        self._client: paramiko.SSHClient | None = None

    def connect(self) -> None:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        if self.strict_host_key_checking:
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        else:
            client.set_missing_host_key_policy(paramiko.WarningPolicy())

        try:
            client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                banner_timeout=self.timeout,
                auth_timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False,
            )
        except paramiko.AuthenticationException as exc:
            raise SSHConnectionError(
                "Credencial SSH invalida. Verifique MIKROTIK_USER e a senha informada."
            ) from exc
        except paramiko.BadHostKeyException as exc:
            raise SSHConnectionError(
                "Host key SSH divergente. Verifique se o IP e do MikroTik esperado."
            ) from exc
        except socket.timeout as exc:
            raise SSHConnectionError(
                "Timeout ao conectar no SSH. Execute: python src/main.py ssh-check"
            ) from exc
        except ConnectionRefusedError as exc:
            raise SSHConnectionError(
                "Porta SSH recusou conexao. Verifique se o servico SSH esta habilitado."
            ) from exc
        except paramiko.SSHException as exc:
            raise SSHConnectionError(
                "Falha SSH. Possivel incompatibilidade de algoritmo, host key ou banner SSH."
            ) from exc
        except OSError as exc:
            raise SSHConnectionError(
                f"Falha ao conectar em {self.host}:{self.port} via SSH: {exc}"
            ) from exc

        self._client = client

    def run_command(self, command: str) -> str:
        safe_command = validate_command(command)
        if self._client is None:
            raise RuntimeError("Cliente SSH nao conectado.")

        try:
            _, stdout, stderr = self._client.exec_command(
                safe_command,
                timeout=self.timeout,
            )
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode("utf-8", errors="replace")
            error = stderr.read().decode("utf-8", errors="replace")
        except (paramiko.SSHException, socket.timeout, OSError) as exc:
            raise RuntimeError(f"Erro ao executar comando read-only: {safe_command}") from exc

        if exit_status != 0:
            raise RuntimeError(
                f"Comando retornou status {exit_status}: {safe_command}\n{error.strip()}"
            )

        if error.strip():
            output = f"{output}\n[stderr]\n{error}".strip()

        return output

    def run_provisioning_command(self, command: str) -> str:
        safe_command = validate_provisioning_command(command, allow_sensitive_password=True)
        if self._client is None:
            raise RuntimeError("Cliente SSH nao conectado.")

        try:
            _, stdout, stderr = self._client.exec_command(
                safe_command,
                timeout=self.timeout,
            )
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode("utf-8", errors="replace")
            error = stderr.read().decode("utf-8", errors="replace")
        except (paramiko.SSHException, socket.timeout, OSError) as exc:
            raise RuntimeError(f"Erro ao executar bloco de provisionamento.") from exc

        if exit_status != 0:
            raise RuntimeError(f"Comando de provisionamento retornou status {exit_status}: {error.strip()}")

        return output

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
