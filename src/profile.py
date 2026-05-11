from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .exceptions import ProfileError


@dataclass(frozen=True)
class ProvisioningProfile:
    path: Path
    data: dict[str, Any]

    @property
    def project_name(self) -> str:
        return str(self.data["project"]["name"])

    @property
    def site_name(self) -> str:
        return str(self.data["project"]["site_name"])

    @property
    def router_identity(self) -> str:
        return str(self.data["management"]["router_identity"])

    @property
    def automation_password_env(self) -> str:
        return str(self.data["management"]["automation_password_env"])


def load_profile(path: Path) -> ProvisioningProfile:
    if not path.exists():
        raise ProfileError(f"Profile nao encontrado: {path}")
    try:
        import yaml
    except ImportError as exc:
        raise ProfileError("Dependencia PyYAML ausente. Execute pip install -r requirements.txt.") from exc

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ProfileError(f"Falha ao ler YAML do profile: {exc}") from exc

    if not isinstance(data, dict):
        raise ProfileError("Profile YAML deve conter um objeto no topo.")

    profile = ProvisioningProfile(path=path, data=data)
    validate_profile(profile)
    return profile


def validate_profile(profile: ProvisioningProfile) -> None:
    data = profile.data
    required_sections = (
        "project",
        "management",
        "interfaces",
        "dhcp_server",
        "dns",
        "services",
        "firewall",
        "hardening",
    )
    for section in required_sections:
        if section not in data or not isinstance(data[section], dict):
            raise ProfileError(f"Secao obrigatoria ausente ou invalida: {section}")

    management = data["management"]
    services = data["services"]
    interfaces = data["interfaces"]
    firewall = data["firewall"]
    hardening = data["hardening"]

    _require_text(management, "router_identity")
    _require_text(management, "automation_user")
    _require_text(management, "automation_group")
    _require_text(management, "automation_password_env")
    _require_text(management, "management_subnet")
    _require_text(management, "management_pc_ip")

    if management["automation_user"].strip().lower() == "admin":
        raise ProfileError("automation_user nao pode ser admin.")

    try:
        management_subnet = ipaddress.ip_network(management["management_subnet"], strict=False)
        management_pc_ip = ipaddress.ip_address(management["management_pc_ip"])
    except ValueError as exc:
        raise ProfileError(f"IP/CIDR de gerenciamento invalido: {exc}") from exc
    if management_pc_ip not in management_subnet:
        raise ProfileError("management_pc_ip deve pertencer a management_subnet.")

    allow_winbox = _cidr_list(management.get("allow_winbox_from", []), "allow_winbox_from")
    allow_ssh = _cidr_list(management.get("allow_ssh_from", []), "allow_ssh_from")
    if not allow_winbox and not allow_ssh:
        raise ProfileError("Defina pelo menos uma origem de gerenciamento para Winbox ou SSH.")
    for network in allow_winbox + allow_ssh:
        if str(network) == "0.0.0.0/0" or str(network) == "::/0":
            raise ProfileError("Gerenciamento nao pode ficar aberto para 0.0.0.0/0.")

    if not _service_enabled(services, "winbox") and not _service_enabled(services, "ssh"):
        raise ProfileError("Nao desabilite winbox e ssh ao mesmo tempo.")
    if _service_enabled(services, "winbox") and not allow_winbox:
        raise ProfileError("Winbox habilitado exige allow_winbox_from.")
    if _service_enabled(services, "ssh") and not allow_ssh:
        raise ProfileError("SSH habilitado exige allow_ssh_from.")
    for name in ("winbox", "ssh"):
        if name in services and "port" in services[name]:
            port = int(services[name]["port"])
            if port < 1 or port > 65535:
                raise ProfileError(f"Porta invalida para {name}: {port}")

    insecure_services = ("www", "www_ssl", "api", "api_ssl", "ftp", "telnet")
    for service in insecure_services:
        if _service_enabled(services, service):
            raise ProfileError(f"Servico inseguro deve ficar desabilitado nesta fase: {service}")

    wan = interfaces.get("wan", {})
    lan_bridge = interfaces.get("lan_bridge", {})
    _require_text(wan, "name")
    _require_text(wan, "type")
    _require_text(lan_bridge, "name")
    _require_text(lan_bridge, "address")
    try:
        lan_address = ipaddress.ip_interface(lan_bridge["address"])
    except ValueError as exc:
        raise ProfileError(f"LAN address invalido: {exc}") from exc
    lan_ports = lan_bridge.get("ports", [])
    if not isinstance(lan_ports, list) or not lan_ports:
        raise ProfileError("lan_bridge.ports deve conter pelo menos uma interface.")
    if wan["name"] in lan_ports or wan["name"] == lan_bridge["name"]:
        raise ProfileError("WAN e LAN nao podem usar a mesma interface.")
    if wan["type"] not in ("dhcp", "pppoe"):
        raise ProfileError("interfaces.wan.type deve ser dhcp ou pppoe.")

    dhcp = data["dhcp_server"]
    if dhcp.get("enabled", False):
        try:
            range_start = ipaddress.ip_address(dhcp["range_start"])
            range_end = ipaddress.ip_address(dhcp["range_end"])
            gateway = ipaddress.ip_address(dhcp["gateway"])
        except ValueError as exc:
            raise ProfileError(f"DHCP IP invalido: {exc}") from exc
        if range_start not in lan_address.network or range_end not in lan_address.network:
            raise ProfileError("Range DHCP deve estar dentro da rede LAN.")
        if gateway not in lan_address.network:
            raise ProfileError("Gateway DHCP deve estar dentro da rede LAN.")
        if int(range_start) > int(range_end):
            raise ProfileError("range_start deve ser menor ou igual a range_end.")

    if firewall.get("enabled") and not firewall.get("drop_all_else_input"):
        raise ProfileError("Firewall input deve ter drop final nesta fase.")
    if firewall.get("nat_masquerade") and not wan.get("name"):
        raise ProfileError("NAT exige WAN definida.")

    if hardening.get("disable_default_admin") and not hardening.get("create_automation_user"):
        raise ProfileError("Nao desabilite admin sem criar usuario de automacao.")


def _require_text(section: dict[str, Any], key: str) -> None:
    if key not in section or not str(section[key]).strip():
        raise ProfileError(f"Campo obrigatorio vazio: {key}")


def _cidr_list(values: Any, field_name: str) -> list[ipaddress._BaseNetwork]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise ProfileError(f"{field_name} deve ser lista.")
    networks = []
    for value in values:
        try:
            networks.append(ipaddress.ip_network(str(value), strict=False))
        except ValueError as exc:
            raise ProfileError(f"CIDR invalido em {field_name}: {value}") from exc
    return networks


def _service_enabled(services: dict[str, Any], name: str) -> bool:
    value = services.get(name, {})
    return bool(isinstance(value, dict) and value.get("enabled", False))
