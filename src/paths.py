from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORTS_DIR = PROJECT_ROOT / "exports"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
GENERATED_DIR = PROJECT_ROOT / "generated"
PROFILES_DIR = PROJECT_ROOT / "profiles"
PROVISIONING_DIR = PROJECT_ROOT / "provisioning"
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE_FILE = PROJECT_ROOT / ".env.example"
GITIGNORE_FILE = PROJECT_ROOT / ".gitignore"


def ensure_runtime_dirs() -> None:
    for path in (EXPORTS_DIR, REPORTS_DIR, LOGS_DIR, GENERATED_DIR, PROFILES_DIR, PROVISIONING_DIR):
        path.mkdir(parents=True, exist_ok=True)
