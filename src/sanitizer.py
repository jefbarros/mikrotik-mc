from __future__ import annotations

import re

SECRET_KEYS: tuple[str, ...] = (
    "password",
    "passwd",
    "pwd",
    "secret",
    "shared-secret",
    "pre-shared-key",
    "key",
    "private-key",
    "token",
    "api-key",
    "apikey",
    "access-token",
    "refresh-token",
    "certificate",
    "identity",
    "auth-key",
    "passphrase",
    "smtp-password",
    "wireguard-private-key",
    "wpa-pre-shared-key",
)

FIELD_NAME_RE = r"[A-Za-z][A-Za-z0-9_.:-]*"
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
SENSITIVE_FIELD_RE = re.compile(
    rf"(?i)\b({'|'.join(re.escape(key) for key in sorted(SECRET_KEYS, key=len, reverse=True))})\s*=\s*"
)


def sanitize_text(text: str, mask_public_ips: bool = False) -> str:
    sanitized = text
    sanitized = _mask_sensitive_fields(sanitized)

    sanitized = EMAIL_RE.sub("***@***.***", sanitized)

    if mask_public_ips:
        sanitized = mask_public_ip_addresses(sanitized)

    return sanitized


def _mask_sensitive_fields(text: str) -> str:
    output: list[str] = []
    position = 0

    while True:
        match = SENSITIVE_FIELD_RE.search(text, position)
        if not match:
            output.append(text[position:])
            break

        value_start = match.end()
        value_end = _find_value_end(text, value_start)
        output.append(text[position:value_start])
        output.append("********")
        position = value_end

    return "".join(output)


def _find_value_end(text: str, start: int) -> int:
    if start >= len(text):
        return start

    quote = text[start] if text[start] in ("'", '"') else ""
    if quote:
        end_quote = text.find(quote, start + 1)
        if end_quote == -1:
            return _line_end(text, start)
        return end_quote + 1

    line_end = _line_end(text, start)
    next_field = re.search(rf"\s+{FIELD_NAME_RE}\s*=", text[start:line_end])
    if next_field:
        return start + next_field.start()
    return line_end


def _line_end(text: str, start: int) -> int:
    newline = text.find("\n", start)
    return len(text) if newline == -1 else newline


def mask_public_ip_addresses(text: str) -> str:
    # Placeholder conservador para fase futura. A fase 1 preserva IPs publicos.
    return text
