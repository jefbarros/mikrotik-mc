from pathlib import Path

from src.main import main
from src.profile import load_profile
from src.provisioner import build_provision_plan, provision_router


EXAMPLE = Path("profiles/example.branch-reset.yaml")


def test_provision_without_flags_does_not_apply(tmp_path, monkeypatch):
    profile = load_profile(EXAMPLE)
    result = provision_router(profile, execute=False, acknowledged=False)
    assert result.applied is False
    assert result.plan.commands_count > 0


def test_provision_with_only_execute_does_not_apply(capsys):
    rc = main(["provision", "--profile", str(EXAMPLE), "--execute"])
    assert rc == 1
    assert "--i-understand-this-changes-router" in capsys.readouterr().out


def test_provision_with_flags_asks_confirmation(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "NAO")
    rc = main([
        "provision",
        "--profile",
        str(EXAMPLE),
        "--execute",
        "--i-understand-this-changes-router",
    ])
    assert rc == 1
    assert "Confirmacao textual invalida" in capsys.readouterr().out


def test_reset_router_always_fails(capsys):
    rc = main(["reset-router"])
    assert rc == 2
    assert "Reset automatico nao implementado" in capsys.readouterr().out


def test_build_plan_creates_markdown():
    profile = load_profile(EXAMPLE)
    plan = build_provision_plan(profile)
    assert plan.plan_path.exists()
    assert plan.rendered.sanitized_path.exists()

