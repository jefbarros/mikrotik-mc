from __future__ import annotations

import re

from .exceptions import SafetyError
from .sanitizer import sanitize_text

FORBIDDEN_SCRIPT_PATTERNS: tuple[str, ...] = (
    r"/system\s+reset-configuration",
    r"/system\s+reboot",
    r"/system\s+shutdown",
    r"/system\s+backup\s+save",
    r"^/import\b",
    r"/tool\s+fetch",
    r"/certificate\s+export",
    r"show-sensitive",
)


def validate_routeros_script(script: str, *, allow_sensitive_password: bool = False) -> None:
    lowered_lines = [line.strip().lower() for line in script.splitlines()]
    for pattern in FORBIDDEN_SCRIPT_PATTERNS:
        if re.search(pattern, script, re.IGNORECASE | re.MULTILINE):
            raise SafetyError(f"Script bloqueado por comando proibido: {pattern}")

    if not allow_sensitive_password and re.search(r"\bpassword\s*=\s*(?!\*\*\*\*\*\*\*\*)\S+", script, re.I):
        raise SafetyError("Script versionavel nao pode conter password real.")

    _validate_firewall_order(lowered_lines)
    _validate_management_restrictions(script)
    sanitize_text(script)


def validate_provisioning_command(command: str, *, allow_sensitive_password: bool = True) -> str:
    normalized = command.strip()
    if not normalized or normalized.startswith("#"):
        raise SafetyError("Comando de provisionamento vazio ou comentario.")
    _validate_forbidden_patterns(normalized)
    if not allow_sensitive_password and re.search(r"\bpassword\s*=\s*(?!\*\*\*\*\*\*\*\*)\S+", normalized, re.I):
        raise SafetyError("Comando versionavel nao pode conter password real.")
    if not normalized.startswith("/"):
        raise SafetyError("Comando de provisionamento deve iniciar com caminho absoluto RouterOS.")
    return normalized


def _validate_forbidden_patterns(script: str) -> None:
    for pattern in FORBIDDEN_SCRIPT_PATTERNS:
        if re.search(pattern, script, re.IGNORECASE | re.MULTILINE):
            raise SafetyError(f"Script bloqueado por comando proibido: {pattern}")


def _validate_firewall_order(lines: list[str]) -> None:
    firewall_lines = [
        (index, line)
        for index, line in enumerate(lines)
        if line.startswith("/ip firewall filter add") and "chain=input" in line
    ]
    if not firewall_lines:
        return

    final_drop_indexes = [
        index
        for index, line in firewall_lines
        if "action=drop" in line and "AUTO-PROVISION input drop final".lower() in line
    ]
    if not final_drop_indexes:
        raise SafetyError("Firewall input precisa ter drop final.")
    final_drop = final_drop_indexes[-1]

    allow_admin_indexes = [
        index
        for index, line in firewall_lines
        if "action=accept" in line and ("dst-port=22" in line or "dst-port=8291" in line)
    ]
    if not allow_admin_indexes:
        raise SafetyError("Firewall precisa permitir administracao antes do drop final.")
    if max(allow_admin_indexes) > final_drop:
        raise SafetyError("Drop final apareceu antes de regra allow administrativa.")


def _validate_management_restrictions(script: str) -> None:
    for service in ("ssh", "winbox"):
        pattern = re.compile(rf"/ip service set {service}\b(.+)", re.I)
        match = pattern.search(script)
        if not match:
            continue
        line = match.group(0).lower()
        if "disabled=no" in line:
            if "address=" not in line:
                raise SafetyError(f"Servico {service} habilitado sem address restritivo.")
            if "address=0.0.0.0/0" in line:
                raise SafetyError(f"Servico {service} aberto para 0.0.0.0/0.")
