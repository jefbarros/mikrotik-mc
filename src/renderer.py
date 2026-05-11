from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .exceptions import RenderError
from .profile import ProvisioningProfile
from .routeros_templates import header
from .safety import validate_routeros_script
from .sanitizer import sanitize_text


@dataclass(frozen=True)
class RenderedScripts:
    sanitized_path: Path
    sensitive_path: Path
    sanitized_script: str
    sensitive_script: str


def render_bootstrap(profile: ProvisioningProfile, generated_dir: Path, *, timestamp: datetime | None = None) -> RenderedScripts:
    return _render(profile, generated_dir, "bootstrap", timestamp=timestamp)


def render_full_config(profile: ProvisioningProfile, generated_dir: Path, *, timestamp: datetime | None = None) -> RenderedScripts:
    return _render(profile, generated_dir, "full_config", timestamp=timestamp)


def _render(
    profile: ProvisioningProfile,
    generated_dir: Path,
    kind: str,
    *,
    timestamp: datetime | None = None,
) -> RenderedScripts:
    generated_dir.mkdir(parents=True, exist_ok=True)
    sensitive_script = "\n".join(_script_lines(profile, kind)).strip() + "\n"
    sanitized_script = sanitize_text(sensitive_script)

    validate_routeros_script(sanitized_script, allow_sensitive_password=False)
    validate_routeros_script(sensitive_script, allow_sensitive_password=True)

    stamp = (timestamp or datetime.now()).strftime("%Y-%m-%d_%H%M%S")
    sanitized_path = generated_dir / f"{stamp}_{kind}_sanitized.rsc"
    sensitive_path = generated_dir / f"{stamp}_{kind}_sensitive.rsc"
    try:
        sanitized_path.write_text(sanitized_script, encoding="utf-8")
        sensitive_path.write_text(sensitive_script, encoding="utf-8")
    except OSError as exc:
        raise RenderError(f"Falha ao gravar scripts gerados: {exc}") from exc

    return RenderedScripts(
        sanitized_path=sanitized_path,
        sensitive_path=sensitive_path,
        sanitized_script=sanitized_script,
        sensitive_script=sensitive_script,
    )


def _script_lines(profile: ProvisioningProfile, kind: str) -> list[str]:
    data = profile.data
    management = data["management"]
    interfaces = data["interfaces"]
    wan = interfaces["wan"]
    lan = interfaces["lan_bridge"]
    dhcp = data["dhcp_server"]
    dns = data["dns"]
    services = data["services"]
    firewall = data["firewall"]
    hardening = data["hardening"]
    log_prefix = data.get("observability", {}).get("log_prefix", "AUTO-PROVISION")
    lan_network = ipaddress.ip_interface(lan["address"]).network
    automation_password = _secret_from_env(management["automation_password_env"])

    lines: list[str] = []
    lines.extend(header(f"{kind} gerado para {profile.site_name}"))
    lines.extend(
        [
            f'/system identity set name="{_ros_quote(management["router_identity"])}"',
            f'/system clock set time-zone-name={management["timezone"]}',
            "",
            f'/interface bridge add name={lan["name"]} comment="{_ros_quote(lan.get("comment", "LAN"))}"',
        ]
    )
    for port in lan["ports"]:
        lines.append(f"/interface bridge port add bridge={lan['name']} interface={port}")
    lines.extend(
        [
            "",
            f'/ip address add address={lan["address"]} interface={lan["name"]} comment="LAN Gateway"',
        ]
    )

    if dhcp.get("enabled"):
        dns_servers = ",".join(dhcp.get("dns_servers", []))
        lines.extend(
            [
                "",
                f'/ip pool add name={dhcp["pool_name"]} ranges={dhcp["range_start"]}-{dhcp["range_end"]}',
                f'/ip dhcp-server add name=dhcp-lan interface={lan["name"]} address-pool={dhcp["pool_name"]} disabled=no',
                f"/ip dhcp-server network add address={lan_network} gateway={dhcp['gateway']} dns-server={dns_servers}",
            ]
        )

    lines.extend(
        [
            "",
            f"/ip dns set allow-remote-requests={'yes' if dns.get('allow_remote_requests') else 'no'} servers={','.join(dns.get('servers', []))}",
            "",
        ]
    )
    if wan["type"] == "dhcp":
        lines.append(f'/ip dhcp-client add interface={wan["name"]} disabled=no comment="{_ros_quote(wan.get("comment", "WAN DHCP"))}"')
    lines.append("")

    if firewall.get("nat_masquerade"):
        lines.append(f'/ip firewall nat add chain=srcnat out-interface={wan["name"]} action=masquerade comment="{log_prefix} NAT LAN via WAN"')
        lines.append("")

    lines.extend(_service_lines(services, management))
    lines.append("")

    if hardening.get("create_automation_user"):
        lines.extend(
            [
                f"/user group add name={management['automation_group']} policy=ssh,read",
                f'/user add name={management["automation_user"]} group={management["automation_group"]} password="{_ros_quote(automation_password)}"',
            ]
        )
    if hardening.get("disable_default_admin"):
        lines.append(f"/user disable {management['admin_user_to_disable']}")
    lines.append("")

    lines.extend(_hardening_lines(wan["name"], log_prefix))
    lines.append("")

    if firewall.get("enabled"):
        lines.extend(_firewall_lines(data, lan_network))

    if kind == "full_config":
        lines.extend(
            [
                "",
                "# VPN, IPsec, load balance e recursos avancados nao sao configurados nesta fase.",
            ]
        )
    return lines


def _service_lines(services: dict[str, Any], management: dict[str, Any]) -> list[str]:
    service_map = {
        "telnet": "telnet",
        "ftp": "ftp",
        "www": "www",
        "www_ssl": "www-ssl",
        "api": "api",
        "api_ssl": "api-ssl",
    }
    lines = [f"/ip service set {routeros_name} disabled=yes" for _, routeros_name in service_map.items()]
    if services["winbox"]["enabled"]:
        lines.append(
            f"/ip service set winbox disabled=no port={int(services['winbox']['port'])} address={','.join(management['allow_winbox_from'])}"
        )
    else:
        lines.append("/ip service set winbox disabled=yes")
    if services["ssh"]["enabled"]:
        lines.append(
            f"/ip service set ssh disabled=no port={int(services['ssh']['port'])} address={','.join(management['allow_ssh_from'])}"
        )
    else:
        lines.append("/ip service set ssh disabled=yes")
    return lines


def _hardening_lines(wan_name: str, log_prefix: str) -> list[str]:
    return [
        "/tool bandwidth-server set enabled=no",
        "/ip neighbor discovery-settings set discover-interface-list=!dynamic",
        f'/ip firewall filter add chain=input action=accept connection-state=established,related,untracked comment="{log_prefix} input established related"',
        f'/ip firewall filter add chain=input action=drop connection-state=invalid comment="{log_prefix} input drop invalid"',
    ]


def _firewall_lines(data: dict[str, Any], lan_network: ipaddress._BaseNetwork) -> list[str]:
    management = data["management"]
    services = data["services"]
    wan_name = data["interfaces"]["wan"]["name"]
    dhcp_enabled = bool(data["dhcp_server"].get("enabled"))
    log_prefix = data.get("observability", {}).get("log_prefix", "AUTO-PROVISION")
    lines: list[str] = []
    lines.append(f'/ip firewall filter add chain=input action=accept protocol=icmp src-address={lan_network} comment="{log_prefix} input ICMP LAN"')
    if dhcp_enabled:
        lines.append(f'/ip firewall filter add chain=input action=accept protocol=udp src-address={lan_network} dst-port=67,68 comment="{log_prefix} input DHCP LAN"')
    if data["dns"].get("allow_remote_requests"):
        lines.append(f'/ip firewall filter add chain=input action=accept protocol=udp src-address={lan_network} dst-port=53 comment="{log_prefix} input DNS UDP LAN"')
        lines.append(f'/ip firewall filter add chain=input action=accept protocol=tcp src-address={lan_network} dst-port=53 comment="{log_prefix} input DNS TCP LAN"')
    if services["winbox"]["enabled"]:
        for source in management["allow_winbox_from"]:
            lines.append(f'/ip firewall filter add chain=input action=accept protocol=tcp src-address={source} dst-port={int(services["winbox"]["port"])} comment="{log_prefix} input Winbox allowed"')
    if services["ssh"]["enabled"]:
        for source in management["allow_ssh_from"]:
            lines.append(f'/ip firewall filter add chain=input action=accept protocol=tcp src-address={source} dst-port={int(services["ssh"]["port"])} comment="{log_prefix} input SSH allowed"')
    lines.append(f'/ip firewall filter add chain=input action=drop in-interface={wan_name} comment="{log_prefix} input drop WAN"')
    lines.append(f'/ip firewall filter add chain=input action=drop comment="{log_prefix} input drop final"')
    return lines


def _secret_from_env(env_name: str) -> str:
    value = os.getenv(env_name, "")
    if not value:
        return f"${{{env_name}}}"
    return value


def _ros_quote(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')

