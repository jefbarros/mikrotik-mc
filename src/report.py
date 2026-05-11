from __future__ import annotations

import re
from pathlib import Path

from .commands import COMMANDS_WITH_SANITIZED_SENSITIVE_OUTPUT
from .collector import CollectionResult
from .exceptions import ReportError
from .sanitizer import sanitize_text


def generate_report(
    result: CollectionResult,
    host: str,
    username: str,
    reports_dir: Path,
    project_name: str = "mikrotik-ai-automation",
) -> Path:
    try:
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"{result.timestamp:%Y-%m-%d_%H%M%S}_relatorio_mikrotik.md"
    except OSError as exc:
        raise ReportError(f"Falha ao preparar diretorio de relatorios: {exc}") from exc

    services = _extract_section(result, "/ip service print detail")
    vpn_summary = _summarize_presence(
        result,
        {
            "PPP secrets": "/ppp secret print detail",
            "PPP active": "/ppp active print detail",
            "L2TP server": "/interface l2tp-server server print detail",
            "OVPN server": "/interface ovpn-server server print detail",
            "SSTP server": "/interface sstp-server server print detail",
        },
    )
    ipsec_summary = _summarize_presence(
        result,
        {
            "IPsec profile": "/ip ipsec profile print detail",
            "IPsec peer": "/ip ipsec peer print detail",
            "IPsec identity": "/ip ipsec identity print detail",
            "IPsec policy": "/ip ipsec policy print detail",
            "IPsec active peers": "/ip ipsec active-peers print detail",
            "IPsec installed SA": "/ip ipsec installed-sa print detail",
        },
    )
    firewall_summary = _summarize_presence(
        result,
        {
            "Firewall filter": "/ip firewall filter print detail",
            "NAT": "/ip firewall nat print detail",
            "Mangle": "/ip firewall mangle print detail",
            "Raw": "/ip firewall raw print detail",
            "Address lists": "/ip firewall address-list print detail",
        },
    )
    route_summary = _route_summary(result)
    service_alerts, service_summary = _service_summary(services)
    command_errors = [item for item in result.command_results if not item.ok]

    content = sanitize_text("\n".join(
        [
            "# Relatorio tecnico MikroTik",
            "",
            f"- Projeto: `{project_name}`",
            f"- Data/hora da coleta: {result.timestamp:%Y-%m-%d %H:%M:%S}",
            f"- Host analisado: `{host}`",
            f"- Usuario SSH usado: `{username}`",
            "- Modo: `read-only`",
            f"- Arquivo de coleta sanitizado: `{result.export_path}`",
            "",
            "## Sumario executivo",
            "",
            f"- Coleta realizada com {result.success_count} comandos concluidos e {result.error_count} comandos com erro.",
            f"- Total de comandos read-only processados: {len(result.command_results)}.",
            "- Dados sensiveis conhecidos foram sanitizados antes da gravacao.",
            "- Interpretacao automatica e conservadora; itens nao reconhecidos ficam como nao avaliados automaticamente.",
            "",
            "## Comandos executados",
            "",
            *[
                f"- `{'OK' if item.ok else 'ERRO'}` `{item.command}`"
                for item in result.command_results
            ],
            "",
            "## Identificacao",
            "",
            _identification_summary(result),
            "",
            "## Servicos",
            "",
            service_summary,
            "",
            "## Interfaces e enderecos",
            "",
            _interfaces_summary(result),
            "",
            "## Rotas",
            "",
            route_summary,
            "",
            "## Firewall",
            "",
            firewall_summary,
            "",
            "## VPN",
            "",
            vpn_summary,
            "",
            "## IPsec",
            "",
            ipsec_summary,
            "",
            "## Logs",
            "",
            _logs_summary(result),
            "",
            "## Alertas preliminares de seguranca",
            "",
            *security_alerts(result, service_alerts, command_errors),
            "",
            "## Proximos passos recomendados",
            "",
            "- Validar que SSH esta restrito por IP de administracao, rede local ou VPN.",
            "- Usar usuario dedicado read-only e evitar o usuario admin.",
            "- Guardar exports sanitizados no Git e revisar `git status` antes de commit.",
            "- Comparar coletas futuras com `python src/main.py diff --before ... --after ...`.",
            "- Nao abrir SSH, API ou REST do RouterOS para a internet.",
            "- Fazer backup real seguro fora deste repositorio; export sanitizado nao substitui backup operacional.",
            "",
            "_Relatorio gerado automaticamente com interpretacao conservadora. Campos nao reconhecidos devem ser tratados como nao avaliados automaticamente nesta versao._",
            "",
        ]
    ))

    try:
        report_path.write_text(content, encoding="utf-8")
        return report_path
    except OSError as exc:
        raise ReportError(f"Falha ao gravar relatorio: {exc}") from exc


def _extract_section(result: CollectionResult, command: str) -> str:
    return result.command_outputs.get(command, "").strip()


def _identification_summary(result: CollectionResult) -> str:
    identity = _extract_section(result, "/system identity print")
    resource = _extract_section(result, "/system resource print")
    routerboard = _extract_section(result, "/system routerboard print")
    packages = _extract_section(result, "/system package print")

    lines = []
    if identity:
        lines.append("- System identity coletado; valores sensiveis foram sanitizados quando aplicavel.")
    if resource:
        lines.append("- Recursos do sistema coletados.")
    if routerboard:
        lines.append("- Informacoes de RouterBOARD coletadas.")
    if packages:
        lines.append("- Pacotes RouterOS coletados; revisar versao no export sanitizado.")

    if not lines:
        return "Nao avaliado automaticamente nesta versao."

    return "\n".join(lines)


def _summarize_presence(result: CollectionResult, commands: dict[str, str]) -> str:
    lines: list[str] = []
    for label, command in commands.items():
        output = _extract_section(result, command)
        count = _approx_rule_count(output)
        if output:
            sensitive_note = (
                " Saida marcada como sensivel sanitizada."
                if command in COMMANDS_WITH_SANITIZED_SENSITIVE_OUTPUT
                else ""
            )
            count_note = f" Quantidade aproximada de entradas: {count}." if count else ""
            lines.append(
                f"- {label}: dados coletados; revisar conteudo sanitizado.{count_note}{sensitive_note}"
            )
        else:
            lines.append(f"- {label}: sem saida coletada ou nao avaliado automaticamente nesta versao.")
    return "\n".join(lines)


def security_alerts(
    result: CollectionResult,
    service_alerts: list[str],
    command_errors: list[object],
) -> list[str]:
    alerts = [
        "- Validar se servicos administrativos estao restritos por origem.",
        "- Validar regras de firewall antes de expor qualquer servico.",
        "- Confirmar que usuarios PPP/IPsec e chaves foram revisados manualmente.",
    ]
    alerts.extend(service_alerts)

    if command_errors:
        alerts.append(f"- {len(command_errors)} comando(s) retornaram erro; revisar export sanitizado.")

    if not _extract_section(result, "/ip service print detail"):
        alerts.append("- Possivel ausencia de dados de `/ip service`; SSH habilitado nao avaliado automaticamente.")
    return alerts


def _service_summary(output: str) -> tuple[list[str], str]:
    if not output:
        return [], "Nao avaliado automaticamente nesta versao."

    alerts: list[str] = []
    lines = ["Saida de `/ip service print detail` coletada."]
    service_blocks = [line.strip() for line in output.splitlines() if line.strip()]
    enabled = [line for line in service_blocks if "disabled=no" in line.lower()]
    if enabled:
        lines.append(f"Servicos aparentemente habilitados: {len(enabled)}.")
        for line in enabled:
            lowered = line.lower()
            if "address=" not in lowered or "address=0.0.0.0/0" in lowered:
                alerts.append(
                    "- Servico administrativo habilitado sem restricao `address=` claramente identificada."
                )
                break
    else:
        lines.append("Servicos habilitados nao avaliados automaticamente.")
    return alerts, "\n".join(f"- {line}" for line in lines)


def _interfaces_summary(result: CollectionResult) -> str:
    interface_output = _extract_section(result, "/interface print detail")
    address_output = _extract_section(result, "/ip address print detail")
    lines: list[str] = []
    if interface_output:
        lines.append(f"- Interfaces coletadas. Quantidade aproximada: {_approx_rule_count(interface_output) or 'nao avaliada'}.")
    else:
        lines.append("- Interfaces nao avaliadas automaticamente nesta versao.")
    if address_output:
        lines.append(f"- Enderecos IP coletados. Quantidade aproximada: {_approx_rule_count(address_output) or 'nao avaliada'}.")
    else:
        lines.append("- Enderecos IP nao avaliados automaticamente nesta versao.")
    return "\n".join(lines)


def _route_summary(result: CollectionResult) -> str:
    output = _extract_section(result, "/ip route print detail")
    if not output:
        return "Nao avaliado automaticamente nesta versao."

    lines = [f"- Rotas coletadas. Quantidade aproximada: {_approx_rule_count(output) or 'nao avaliada'}."]
    if "dst-address=0.0.0.0/0" in output or "0.0.0.0/0" in output:
        lines.append("- Indicio de default route observado.")
    if output.count("dst-address=0.0.0.0/0") > 1 or output.count("0.0.0.0/0") > 1:
        lines.append("- Mais de uma default route pode existir; nao concluir balanceamento sem revisao manual.")
    return "\n".join(lines)


def _logs_summary(result: CollectionResult) -> str:
    commands = {
        "IPsec": '/log print where topics~"ipsec"',
        "L2TP": '/log print where topics~"l2tp"',
        "Error": '/log print where topics~"error"',
    }
    lines: list[str] = []
    for label, command in commands.items():
        output = _extract_section(result, command)
        if output:
            failure_note = " Eventos com erro/falha observados." if re.search(r"fail|error|erro", output, re.I) else ""
            lines.append(f"- {label}: eventos coletados.{failure_note}")
        else:
            lines.append(f"- {label}: sem eventos coletados ou nao avaliado automaticamente.")
    return "\n".join(lines)


def _approx_rule_count(output: str) -> int:
    count = 0
    for line in output.splitlines():
        if re.match(r"^\s*\d+\s", line) or re.match(r"^\s*\d+\s+[A-Z]", line):
            count += 1
    return count
