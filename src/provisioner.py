from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import load_settings
from .diff import generate_diff_report
from .doctor import check_ssh_tcp
from .exceptions import ProvisioningError
from .logger import safe_log, setup_logger
from .paths import EXPORTS_DIR, GENERATED_DIR, PROVISIONING_DIR, REPORTS_DIR
from .profile import ProvisioningProfile
from .renderer import RenderedScripts, render_full_config
from .safety import validate_provisioning_command
from .sanitizer import sanitize_text


@dataclass(frozen=True)
class ProvisionPlan:
    rendered: RenderedScripts
    plan_path: Path
    commands_count: int


@dataclass(frozen=True)
class ProvisionResult:
    plan: ProvisionPlan
    applied: bool
    report_path: Path | None = None
    before_export: Path | None = None
    after_export: Path | None = None
    diff_report: Path | None = None


def build_provision_plan(profile: ProvisioningProfile) -> ProvisionPlan:
    rendered = render_full_config(profile, GENERATED_DIR)
    commands = split_routeros_commands(rendered.sensitive_script)
    for command in commands:
        validate_provisioning_command(command, allow_sensitive_password=True)
    plan_path = _write_plan(profile, rendered, len(commands))
    return ProvisionPlan(rendered=rendered, plan_path=plan_path, commands_count=len(commands))


def provision_router(
    profile: ProvisioningProfile,
    *,
    execute: bool,
    acknowledged: bool,
    confirmation: str | None = None,
) -> ProvisionResult:
    plan = build_provision_plan(profile)
    if not execute:
        return ProvisionResult(plan=plan, applied=False)
    if not acknowledged:
        raise ProvisioningError("Provisionamento exige --i-understand-this-changes-router.")
    if confirmation != "APLICAR":
        raise ProvisioningError("Confirmacao textual invalida. Digite APLICAR para continuar.")
    env_name = profile.automation_password_env
    if not os.getenv(env_name):
        raise ProvisioningError(f"Variavel de ambiente obrigatoria ausente para aplicacao: {env_name}")

    logger = setup_logger()
    safe_log(logger, logging.INFO, "Inicio do provisionamento controlado")

    settings = load_settings(require_password=True, prompt_for_password=True)
    ok, detail = check_ssh_tcp(settings.host, settings.ssh_port, settings.timeout)
    if not ok:
        raise ProvisioningError(f"Porta SSH inacessivel antes do provisionamento: {detail}")

    from .collector import collect_routeros_data
    from .report import generate_report
    from .ssh_client import RouterOSSSHClient

    client = RouterOSSSHClient(
        host=settings.host,
        port=settings.ssh_port,
        username=settings.user,
        password=settings.password or "",
        timeout=settings.timeout,
        strict_host_key_checking=settings.strict_host_key_checking,
    )
    before_export: Path | None = None
    after_export: Path | None = None
    diff_report: Path | None = None
    report_path: Path | None = None
    try:
        client.connect()
        before = collect_routeros_data(client, EXPORTS_DIR, logger=logger)
        before_export = before.export_path
        for command in split_routeros_commands(plan.rendered.sensitive_script):
            safe_log(logger, logging.INFO, "Aplicando comando de provisionamento: %s", sanitize_text(command))
            client.run_provisioning_command(command)
        after = collect_routeros_data(client, EXPORTS_DIR, logger=logger)
        after_export = after.export_path
        report_path = generate_report(after, settings.host, settings.user, REPORTS_DIR, project_name=settings.project_name)
        diff_report = generate_diff_report(before_export, after_export, REPORTS_DIR).report_path
    finally:
        client.close()

    safe_log(logger, logging.INFO, "Provisionamento controlado concluido")
    return ProvisionResult(
        plan=plan,
        applied=True,
        report_path=report_path,
        before_export=before_export,
        after_export=after_export,
        diff_report=diff_report,
    )


def split_routeros_commands(script: str) -> list[str]:
    commands: list[str] = []
    for line in script.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        commands.append(stripped)
    return commands


def _write_plan(profile: ProvisioningProfile, rendered: RenderedScripts, commands_count: int) -> Path:
    PROVISIONING_DIR.mkdir(parents=True, exist_ok=True)
    path = PROVISIONING_DIR / f"{datetime.now():%Y-%m-%d_%H%M%S}_provision_plan.md"
    content = "\n".join(
        [
            "# Plano de provisionamento MikroTik",
            "",
            f"- Profile: `{profile.path}`",
            f"- Site: `{profile.site_name}`",
            f"- Identidade alvo: `{profile.router_identity}`",
            "- Modo padrao: render/dry-run",
            f"- Comandos RouterOS planejados: {commands_count}",
            f"- Script sanitizado: `{rendered.sanitized_path}`",
            f"- Script sensivel local: `{rendered.sensitive_path}`",
            "",
            "## Controles de seguranca",
            "",
            "- Aplicacao via SSH exige `--execute` e `--i-understand-this-changes-router`.",
            "- Aplicacao exige confirmacao textual `APLICAR`.",
            "- Script foi validado contra comandos proibidos de reset, reboot, import, fetch e export sensivel.",
            "- Revise o `.rsc` sanitizado antes de aplicar.",
            "",
        ]
    )
    path.write_text(sanitize_text(content), encoding="utf-8")
    return path
