from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from src.collector import dry_run_commands
    from src.commands import READ_ONLY_COMMANDS, validate_all_commands
    from src.config import load_settings
    from src.diff import generate_diff_report
    from src.doctor import check_ssh_tcp, run_doctor
    from src.exceptions import MikrotikAutomationError
    from src.logger import safe_log, setup_logger
    from src.paths import EXPORTS_DIR, GENERATED_DIR, REPORTS_DIR, ensure_runtime_dirs
else:
    from .collector import dry_run_commands
    from .commands import READ_ONLY_COMMANDS, validate_all_commands
    from .config import load_settings
    from .diff import generate_diff_report
    from .doctor import check_ssh_tcp, run_doctor
    from .exceptions import MikrotikAutomationError
    from .logger import safe_log, setup_logger
    from .paths import EXPORTS_DIR, GENERATED_DIR, REPORTS_DIR, ensure_runtime_dirs

PROJECT_NAME = "mikrotik-ai-automation"
VERSION = "2.0.0"
MODE = "read-only production + controlled provisioning"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mikrotik-ai-automation",
        description="Coleta read-only via SSH para MikroTik RouterOS.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    collect_parser = subparsers.add_parser("collect", help="Executa coleta read-only.")
    collect_parser.add_argument(
        "--execute",
        action="store_true",
        help="Confirma conexao SSH e execucao dos comandos read-only. Sem isso, roda em dry-run.",
    )
    subparsers.add_parser("doctor", help="Valida ambiente local e .env sem imprimir segredos.")
    subparsers.add_parser("ssh-check", help="Testa apenas TCP host:porta, sem senha e sem login.")
    subparsers.add_parser("validate-commands", help="Valida allowlist e denylist read-only.")
    diff_parser = subparsers.add_parser("diff", help="Compara duas coletas sanitizadas.")
    diff_parser.add_argument("--before", required=True, help="Arquivo de coleta antigo.")
    diff_parser.add_argument("--after", required=True, help="Arquivo de coleta novo.")
    subparsers.add_parser("version", help="Mostra versao interna.")
    subparsers.add_parser("apply", help="Placeholder bloqueado para fase futura.")
    validate_profile_parser = subparsers.add_parser("validate-profile", help="Valida profile YAML de provisionamento.")
    validate_profile_parser.add_argument("--profile", required=True, help="Caminho do profile YAML.")
    render_bootstrap_parser = subparsers.add_parser("render-bootstrap", help="Gera bootstrap .rsc sem conectar no MikroTik.")
    render_bootstrap_parser.add_argument("--profile", required=True, help="Caminho do profile YAML.")
    render_config_parser = subparsers.add_parser("render-config", help="Gera configuracao completa .rsc sem conectar no MikroTik.")
    render_config_parser.add_argument("--profile", required=True, help="Caminho do profile YAML.")
    provision_parser = subparsers.add_parser("provision", help="Provisionamento controlado via SSH.")
    provision_parser.add_argument("--profile", required=True, help="Caminho do profile YAML.")
    provision_parser.add_argument("--execute", action="store_true", help="Permite aplicar via SSH quando combinado com a flag de entendimento.")
    provision_parser.add_argument(
        "--i-understand-this-changes-router",
        action="store_true",
        help="Reconhece que o provisionamento altera o roteador.",
    )
    subparsers.add_parser("reset-router", help="Sempre bloqueado nesta fase.")

    args = parser.parse_args(argv)
    ensure_runtime_dirs()

    if args.command == "collect":
        return run_collect(execute=args.execute)
    if args.command == "doctor":
        return run_doctor_cli()
    if args.command == "ssh-check":
        return run_ssh_check()
    if args.command == "validate-commands":
        return run_validate_commands()
    if args.command == "diff":
        return run_diff(Path(args.before), Path(args.after))
    if args.command == "version":
        print(f"{PROJECT_NAME} {VERSION}")
        print(f"Modo: {MODE}")
        return 0
    if args.command == "apply":
        print("Aplicacao de mudancas nao implementada nesta fase read-only.")
        return 2
    if args.command == "validate-profile":
        return run_validate_profile(Path(args.profile))
    if args.command == "render-bootstrap":
        return run_render_bootstrap(Path(args.profile))
    if args.command == "render-config":
        return run_render_config(Path(args.profile))
    if args.command == "provision":
        return run_provision(
            Path(args.profile),
            execute=args.execute,
            acknowledged=args.i_understand_this_changes_router,
        )
    if args.command == "reset-router":
        print("Reset automatico nao implementado por seguranca. Faca reset manualmente e use render-bootstrap.")
        return 2

    parser.print_help()
    return 1


def run_collect(execute: bool = False) -> int:
    if not execute:
        try:
            commands = dry_run_commands()
        except MikrotikAutomationError as exc:
            print(f"ERRO: {exc}")
            return 1
        print("DRY-RUN: nenhuma conexao SSH foi aberta e nenhum comando foi enviado.")
        print(f"Comandos read-only que seriam executados ({len(commands)}):")
        for command in commands:
            print(f"- {command}")
        print("Para executar a coleta real read-only, use: python src/main.py collect --execute")
        return 0

    logger = setup_logger()
    safe_log(logger, logging.INFO, "Inicio da coleta read-only")
    client = None

    try:
        from src.collector import collect_routeros_data
        from src.report import generate_report
        from src.ssh_client import RouterOSSSHClient

        settings = load_settings(require_password=True, prompt_for_password=True)
        print(f"Conectando em {settings.host}:{settings.ssh_port} via SSH...")
        if not settings.strict_host_key_checking:
            print("Aviso: strict host key checking esta desativado; use apenas em rede local/VPN confiavel.")
        client = RouterOSSSHClient(
            host=settings.host,
            port=settings.ssh_port,
            username=settings.user,
            password=settings.password or "",
            timeout=settings.timeout,
            strict_host_key_checking=settings.strict_host_key_checking,
        )
        client.connect()
        result = collect_routeros_data(client, EXPORTS_DIR, logger=logger)
        report_path = generate_report(
            result,
            settings.host,
            settings.user,
            REPORTS_DIR,
            project_name=settings.project_name,
        )
    except MikrotikAutomationError as exc:
        safe_log(logger, logging.ERROR, "Falha na coleta: %s", exc)
        print(f"ERRO: {exc}")
        return 1
    except Exception as exc:
        safe_log(logger, logging.ERROR, "Falha inesperada na coleta: %s", exc)
        print(f"ERRO inesperado: {exc}")
        return 1
    finally:
        if client is not None:
            client.close()

    safe_log(logger, logging.INFO, "Coleta read-only concluida")
    safe_log(logger, logging.INFO, "Export sanitizado: %s", result.export_path)
    safe_log(logger, logging.INFO, "Relatorio Markdown: %s", report_path)
    print("Coleta read-only concluida.")
    print(f"Export sanitizado: {result.export_path}")
    print(f"Relatorio Markdown: {report_path}")
    return 0


def run_doctor_cli() -> int:
    print("Diagnostico local")
    results = run_doctor()
    for result in results:
        status = "OK" if result.ok else "FALHA"
        print(f"[{status}] {result.name}: {result.detail}")
    return 0 if all(result.ok for result in results if result.name != "Python da venv") else 1


def run_ssh_check() -> int:
    try:
        settings = load_settings(require_password=False, require_env=True)
    except MikrotikAutomationError as exc:
        print(f"ERRO: {exc}")
        return 1

    ok, detail = check_ssh_tcp(settings.host, settings.ssh_port, settings.timeout)
    print(detail)
    if ok:
        return 0
    print("Sugestoes:")
    print("- No MikroTik, verificar: /ip service print detail where name=ssh")
    print("- Verificar firewall input.")
    print("- Verificar address= em /ip service.")
    print("- Confirmar IP correto do MikroTik.")
    print("- Confirmar conectividade via VPN ou rede local.")
    return 1


def run_validate_commands() -> int:
    try:
        validate_all_commands()
    except MikrotikAutomationError as exc:
        print(f"ERRO: {exc}")
        return 1
    print(f"Allowlist read-only validada com sucesso: {len(READ_ONLY_COMMANDS)} comandos.")
    return 0


def run_diff(before: Path, after: Path) -> int:
    try:
        result = generate_diff_report(before, after, REPORTS_DIR)
    except Exception as exc:
        print(f"ERRO: {exc}")
        return 1
    print(f"Relatorio de diff gerado: {result.report_path}")
    print(f"Secoes alteradas: {result.changed_sections}")
    return 0


def run_validate_profile(profile_path: Path) -> int:
    try:
        from src.profile import load_profile

        load_profile(profile_path)
    except Exception as exc:
        print(f"ERRO: {exc}")
        return 1
    print(f"Profile validado com sucesso: {profile_path}")
    return 0


def run_render_bootstrap(profile_path: Path) -> int:
    try:
        from src.profile import load_profile
        from src.renderer import render_bootstrap

        profile = load_profile(profile_path)
        rendered = render_bootstrap(profile, GENERATED_DIR)
    except Exception as exc:
        print(f"ERRO: {exc}")
        return 1
    print(f"Bootstrap sanitizado: {rendered.sanitized_path}")
    print(f"Bootstrap sensivel local: {rendered.sensitive_path}")
    print("Nao commite o arquivo sensivel.")
    print("Cole este script no Winbox Terminal se a RB estiver sem IP/SSH.")
    return 0


def run_render_config(profile_path: Path) -> int:
    try:
        from src.profile import load_profile
        from src.renderer import render_full_config

        profile = load_profile(profile_path)
        rendered = render_full_config(profile, GENERATED_DIR)
    except Exception as exc:
        print(f"ERRO: {exc}")
        return 1
    print(f"Config sanitizada: {rendered.sanitized_path}")
    print(f"Config sensivel local: {rendered.sensitive_path}")
    print("Nao commite o arquivo sensivel.")
    return 0


def run_provision(profile_path: Path, *, execute: bool, acknowledged: bool) -> int:
    try:
        from src.profile import load_profile
        from src.provisioner import provision_router

        profile = load_profile(profile_path)
        if execute and not acknowledged:
            print("ERRO: provisionamento exige --i-understand-this-changes-router.")
            return 1
        confirmation = None
        if execute:
            confirmation = input("DIGITE APLICAR para continuar: ")
        result = provision_router(
            profile,
            execute=execute,
            acknowledged=acknowledged,
            confirmation=confirmation,
        )
    except Exception as exc:
        print(f"ERRO: {exc}")
        return 1

    print(f"Plano de provisionamento: {result.plan.plan_path}")
    print(f"Script sanitizado: {result.plan.rendered.sanitized_path}")
    print(f"Script sensivel local: {result.plan.rendered.sensitive_path}")
    print(f"Comandos planejados: {result.plan.commands_count}")
    if not result.applied:
        print("SIMULACAO: nenhuma conexao SSH foi aberta e nenhum comando foi aplicado.")
        return 0
    print("Provisionamento aplicado via SSH.")
    print(f"Export antes: {result.before_export}")
    print(f"Export depois: {result.after_export}")
    print(f"Relatorio final: {result.report_path}")
    print(f"Relatorio diff: {result.diff_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
