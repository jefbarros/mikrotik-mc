from __future__ import annotations

from .exceptions import CommandValidationError

READ_ONLY_COMMANDS: tuple[str, ...] = (
    "/system identity print",
    "/system resource print",
    "/system routerboard print",
    "/system package print",
    "/system clock print",
    "/ip service print detail",
    "/ip address print detail",
    "/ip route print detail",
    "/ip dns print detail",
    "/ip firewall filter print detail",
    "/ip firewall nat print detail",
    "/ip firewall mangle print detail",
    "/ip firewall raw print detail",
    "/ip firewall address-list print detail",
    "/interface print detail",
    "/interface bridge print detail",
    "/interface vlan print detail",
    "/interface pppoe-client print detail",
    "/ppp profile print detail",
    "/ppp secret print detail",
    "/ppp active print detail",
    "/interface l2tp-server server print detail",
    "/interface ovpn-server server print detail",
    "/interface sstp-server server print detail",
    "/ip ipsec profile print detail",
    "/ip ipsec peer print detail",
    "/ip ipsec identity print detail",
    "/ip ipsec proposal print detail",
    "/ip ipsec policy print detail",
    "/ip ipsec active-peers print detail",
    "/ip ipsec installed-sa print detail",
    '/log print where topics~"ipsec"',
    '/log print where topics~"l2tp"',
    '/log print where topics~"error"',
    "/export terse",
)

DANGEROUS_TERMS: tuple[str, ...] = (
    "add",
    "set",
    "remove",
    "disable",
    "enable",
    "reset",
    "reboot",
    "shutdown",
    "password",
    "secret",
    "sensitive",
    "import",
    "export file",
    "system backup save",
    "certificate export",
    "user export",
)

ALLOWLISTED_SENSITIVE_MENU_COMMANDS: tuple[str, ...] = (
    "/ppp secret print detail",
)

COMMANDS_WITH_SANITIZED_SENSITIVE_OUTPUT: tuple[str, ...] = (
    "/ppp secret print detail",
    "/ip ipsec identity print detail",
    "/ip ipsec profile print detail",
    "/ip ipsec peer print detail",
    "/export terse",
)


def validate_command(command: str) -> str:
    normalized = " ".join(command.strip().split())

    if normalized not in normalized_read_only_commands():
        raise CommandValidationError(
            f"Comando bloqueado pela politica de seguranca: fora da allowlist read-only."
        )

    lowered = normalized.lower()
    for term in DANGEROUS_TERMS:
        if normalized in ALLOWLISTED_SENSITIVE_MENU_COMMANDS and term == "secret":
            continue
        if _contains_term(lowered, term):
            raise CommandValidationError(
                f"Comando bloqueado pela politica de seguranca: termo perigoso '{term}'."
            )

    if not _is_read_only_shape(lowered):
        raise CommandValidationError(
            "Comando bloqueado pela politica de seguranca: formato nao read-only."
        )

    return normalized


def _contains_term(command: str, term: str) -> bool:
    if " " in term:
        return term in command

    tokens = (
        command.replace("/", " ")
        .replace("=", " ")
        .replace(";", " ")
        .replace(",", " ")
        .replace('"', " ")
        .split()
    )
    return term in tokens


def validate_all_commands() -> None:
    for command in READ_ONLY_COMMANDS:
        validate_command(command)


def normalized_read_only_commands() -> set[str]:
    return {" ".join(item.strip().split()) for item in READ_ONLY_COMMANDS}


def _is_read_only_shape(command: str) -> bool:
    if command == "/export terse":
        return True
    if command.startswith("/log print where "):
        return True
    return " print" in command and not any(
        blocked in command
        for blocked in (" file=", " show-sensitive", " without-paging")
    )
