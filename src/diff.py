from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .exceptions import ReportError
from .sanitizer import sanitize_text

SECTION_RE = re.compile(r"^=== COMMAND: (.+?) ===\s*$")


@dataclass(frozen=True)
class DiffResult:
    report_path: Path
    changed_sections: int


def generate_diff_report(before: Path, after: Path, reports_dir: Path) -> DiffResult:
    if not before.exists():
        raise FileNotFoundError(f"Arquivo before nao encontrado: {before}")
    if not after.exists():
        raise FileNotFoundError(f"Arquivo after nao encontrado: {after}")

    before_sections = parse_export_sections(sanitize_text(before.read_text(encoding="utf-8")))
    after_sections = parse_export_sections(sanitize_text(after.read_text(encoding="utf-8")))
    commands = sorted(set(before_sections) | set(after_sections))

    chunks: list[str] = [
        "# Relatorio de diferencas MikroTik",
        "",
        f"- Data/hora: {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"- Antes: `{before}`",
        f"- Depois: `{after}`",
        "- Conteudo sanitizado novamente antes da comparacao.",
        "",
    ]
    changed = 0
    for command in commands:
        before_text = before_sections.get(command, "").splitlines()
        after_text = after_sections.get(command, "").splitlines()
        if before_text == after_text:
            continue
        changed += 1
        diff_lines = list(
            difflib.unified_diff(
                before_text,
                after_text,
                fromfile="before",
                tofile="after",
                lineterm="",
            )
        )
        chunks.extend(
            [
                f"## {command}",
                "",
                "```diff",
                *diff_lines,
                "```",
                "",
            ]
        )

    if changed == 0:
        chunks.append("Nenhuma diferenca encontrada nas secoes coletadas.")

    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{datetime.now():%Y-%m-%d_%H%M%S}_diff_mikrotik.md"
    try:
        report_path.write_text(sanitize_text("\n".join(chunks)), encoding="utf-8")
    except OSError as exc:
        raise ReportError(f"Falha ao gravar relatorio de diff: {exc}") from exc

    return DiffResult(report_path=report_path, changed_sections=changed)


def parse_export_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_command: str | None = None
    for line in text.splitlines():
        match = SECTION_RE.match(line)
        if match:
            current_command = match.group(1)
            sections.setdefault(current_command, [])
            continue
        if current_command is not None:
            sections[current_command].append(line)
    return {command: "\n".join(lines).strip() for command, lines in sections.items()}

