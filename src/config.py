from __future__ import annotations

from dataclasses import dataclass
from getpass import getpass
from pathlib import Path

from .exceptions import ConfigError
from .paths import ENV_FILE, PROJECT_ROOT


@dataclass(frozen=True)
class Settings:
    host: str
    ssh_port: int
    user: str
    password: str | None
    timeout: int
    strict_host_key_checking: bool
    project_name: str
    project_root: Path


def load_settings(
    project_root: Path | None = None,
    *,
    require_password: bool,
    prompt_for_password: bool = False,
    require_env: bool = True,
) -> Settings:
    root = project_root or PROJECT_ROOT
    env_path = root / ".env"
    values = load_env_values(env_path, require_env=require_env)

    host = _required(values, "MIKROTIK_HOST")
    user = _required(values, "MIKROTIK_USER")
    password = values.get("MIKROTIK_PASSWORD", "").strip()
    ssh_port = _int_value(values, "MIKROTIK_SSH_PORT", default=22, minimum=1, maximum=65535)
    timeout = _int_value(values, "MIKROTIK_TIMEOUT", default=15, minimum=1, maximum=300)
    strict_host_key_checking = _bool_value(
        values, "MIKROTIK_STRICT_HOST_KEY_CHECKING", default=False
    )
    project_name = values.get("PROJECT_NAME", "mikrotik-ai-automation").strip()

    if require_password and not password and prompt_for_password:
        password = getpass("Senha SSH do MikroTik: ")

    if require_password and not password:
        raise ConfigError("MIKROTIK_PASSWORD nao informado e senha interativa vazia.")

    return Settings(
        host=host,
        ssh_port=ssh_port,
        user=user,
        password=password or None,
        timeout=timeout,
        strict_host_key_checking=strict_host_key_checking,
        project_name=project_name,
        project_root=root,
    )


def load_env_values(
    env_path: Path | None = None,
    *,
    require_env: bool = True,
) -> dict[str, str]:
    path = env_path or ENV_FILE
    if not path.exists():
        if require_env:
            raise ConfigError(".env nao encontrado. Copie .env.example para .env.")
        return {}

    try:
        from dotenv import dotenv_values
    except ImportError:
        return _parse_env_without_dependency(path)

    raw_values = dotenv_values(path)
    return {key: str(value or "") for key, value in raw_values.items() if key}


def _parse_env_without_dependency(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _required(values: dict[str, str], name: str) -> str:
    value = values.get(name, "").strip()
    if not value:
        raise ConfigError(f"Variavel obrigatoria ausente no .env: {name}")
    return value


def _int_value(
    values: dict[str, str],
    name: str,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    raw = values.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} deve ser inteiro. Valor recebido: {raw}") from exc

    if value < minimum or value > maximum:
        raise ConfigError(f"{name} deve estar entre {minimum} e {maximum}.")

    return value


def _bool_value(values: dict[str, str], name: str, *, default: bool) -> bool:
    raw = values.get(name, str(default)).strip().lower()
    if raw in ("1", "true", "yes", "y", "sim", "s"):
        return True
    if raw in ("0", "false", "no", "n", "nao"):
        return False
    raise ConfigError(f"{name} deve ser true ou false.")
