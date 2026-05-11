from pathlib import Path
import subprocess

from src.profile import load_profile
from src.renderer import render_bootstrap, render_full_config


EXAMPLE = Path("profiles/example.branch-reset.yaml")


def test_render_bootstrap_does_not_include_secret_in_sanitized(monkeypatch, tmp_path):
    monkeypatch.setenv("MIKROTIK_AUTOMATION_PASSWORD", "SenhaReal123")
    profile = load_profile(EXAMPLE)
    rendered = render_bootstrap(profile, tmp_path)
    sanitized = rendered.sanitized_path.read_text(encoding="utf-8")
    sensitive = rendered.sensitive_path.read_text(encoding="utf-8")
    assert "SenhaReal123" not in sanitized
    assert "password=********" in sanitized
    assert "SenhaReal123" in sensitive


def test_render_full_config_generates_rsc(tmp_path):
    profile = load_profile(EXAMPLE)
    rendered = render_full_config(profile, tmp_path)
    assert rendered.sanitized_path.exists()
    assert rendered.sensitive_path.exists()
    assert "/ip firewall filter add" in rendered.sanitized_script


def test_firewall_drop_final_after_management_allow(tmp_path):
    profile = load_profile(EXAMPLE)
    rendered = render_bootstrap(profile, tmp_path)
    lines = rendered.sanitized_script.splitlines()
    allow_indexes = [
        idx for idx, line in enumerate(lines)
        if "input SSH allowed" in line or "input Winbox allowed" in line
    ]
    drop_index = next(idx for idx, line in enumerate(lines) if "input drop final" in line)
    assert allow_indexes
    assert max(allow_indexes) < drop_index


def test_sensitive_generated_file_is_ignored_by_git(tmp_path):
    result = subprocess.run(
        ["git", "check-ignore", "-q", "generated/test_sensitive.rsc"],
        cwd=Path.cwd(),
        check=False,
    )
    assert result.returncode == 0
