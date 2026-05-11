from pathlib import Path

import pytest

from src.config import ConfigError, load_settings
from src.main import main


def write_env(root: Path, extra: str = "") -> None:
    (root / ".env").write_text(
        "\n".join(
            [
                "MIKROTIK_HOST=192.168.88.1",
                "MIKROTIK_SSH_PORT=22",
                "MIKROTIK_USER=ia-automation",
                "MIKROTIK_PASSWORD=",
                "MIKROTIK_TIMEOUT=15",
                "MIKROTIK_STRICT_HOST_KEY_CHECKING=false",
                "PROJECT_NAME=mikrotik-ai-automation",
                extra,
            ]
        ),
        encoding="utf-8",
    )


def test_load_settings_without_password_when_not_required(tmp_path):
    write_env(tmp_path)
    settings = load_settings(tmp_path, require_password=False)
    assert settings.host == "192.168.88.1"
    assert settings.password is None


def test_invalid_port_fails(tmp_path):
    write_env(tmp_path, "MIKROTIK_SSH_PORT=abc")
    with pytest.raises(ConfigError):
        load_settings(tmp_path, require_password=False)


def test_invalid_timeout_fails(tmp_path):
    write_env(tmp_path, "MIKROTIK_TIMEOUT=0")
    with pytest.raises(ConfigError):
        load_settings(tmp_path, require_password=False)


def test_dry_run_does_not_require_password(capsys):
    assert main(["collect"]) == 0
    output = capsys.readouterr().out
    assert "DRY-RUN" in output
    assert "Senha SSH" not in output

