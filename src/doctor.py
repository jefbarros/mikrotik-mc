from __future__ import annotations

import importlib.util
import socket
import sys
from dataclasses import dataclass
from pathlib import Path

from .config import ConfigError, load_env_values
from .paths import ENV_EXAMPLE_FILE, ENV_FILE, EXPORTS_DIR, GITIGNORE_FILE, LOGS_DIR, PROJECT_ROOT, REPORTS_DIR


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def run_doctor() -> list[CheckResult]:
    results: list[CheckResult] = []
    results.append(CheckResult("Python", sys.version_info >= (3, 11), sys.version.split()[0]))
    results.append(CheckResult("Diretorio atual", Path.cwd() == PROJECT_ROOT, str(Path.cwd())))
    results.append(CheckResult(".env", ENV_FILE.exists(), str(ENV_FILE)))
    results.append(CheckResult(".env.example", ENV_EXAMPLE_FILE.exists(), str(ENV_EXAMPLE_FILE)))
    results.append(CheckResult(".env no .gitignore", _gitignore_contains(".env"), ".env deve estar ignorado"))
    for path in (EXPORTS_DIR, REPORTS_DIR, LOGS_DIR):
        results.append(CheckResult(path.name, path.exists(), str(path)))

    venv_dir = PROJECT_ROOT / ".venv"
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    results.append(CheckResult(".venv existe", venv_dir.exists(), str(venv_dir)))
    results.append(
        CheckResult(
            "Python da venv",
            in_venv or ".venv" in sys.executable.lower(),
            sys.executable,
        )
    )

    for module in ("paramiko", "dotenv", "pytest"):
        results.append(
            CheckResult(
                f"Modulo {module}",
                importlib.util.find_spec(module) is not None,
                "instalado" if importlib.util.find_spec(module) else "nao encontrado",
            )
        )

    try:
        env = load_env_values(require_env=True)
        results.append(CheckResult("MIKROTIK_HOST", bool(env.get("MIKROTIK_HOST", "").strip()), "configurado" if env.get("MIKROTIK_HOST") else "ausente"))
        port = int(env.get("MIKROTIK_SSH_PORT", ""))
        results.append(CheckResult("MIKROTIK_SSH_PORT", 1 <= port <= 65535, str(port)))
        results.append(CheckResult("MIKROTIK_USER", bool(env.get("MIKROTIK_USER", "").strip()), "configurado" if env.get("MIKROTIK_USER") else "ausente"))
        results.append(
            CheckResult(
                "MIKROTIK_PASSWORD",
                True,
                "configurado ou sera solicitado apenas em collect --execute",
            )
        )
    except (ConfigError, ValueError) as exc:
        results.append(CheckResult(".env valido", False, str(exc)))

    return results


def check_ssh_tcp(host: str, port: int, timeout: int) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, f"Porta TCP acessivel em {host}:{port}."
    except OSError as exc:
        return False, f"Porta TCP inacessivel em {host}:{port}: {exc}"


def _gitignore_contains(pattern: str) -> bool:
    if not GITIGNORE_FILE.exists():
        return False
    lines = [line.strip() for line in GITIGNORE_FILE.read_text(encoding="utf-8").splitlines()]
    return pattern in lines

