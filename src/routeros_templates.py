from __future__ import annotations


def header(title: str) -> list[str]:
    return [
        "# mikrotik-ai-automation",
        f"# {title}",
        "# Revise antes de aplicar. Nao commite arquivos sensitive.",
        "",
    ]

