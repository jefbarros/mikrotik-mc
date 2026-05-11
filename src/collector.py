from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from typing import Protocol

from .commands import READ_ONLY_COMMANDS, validate_all_commands
from .exceptions import CollectionError
from .logger import safe_log
from .sanitizer import sanitize_text


class CommandRunner(Protocol):
    def run_command(self, command: str) -> str:
        ...


@dataclass(frozen=True)
class CommandResult:
    command: str
    output: str
    ok: bool = True
    error: str | None = None


@dataclass(frozen=True)
class CollectionResult:
    timestamp: datetime
    export_path: Path
    command_results: list[CommandResult]

    @property
    def command_outputs(self) -> dict[str, str]:
        return {item.command: item.output for item in self.command_results}

    @property
    def error_count(self) -> int:
        return sum(1 for item in self.command_results if not item.ok)

    @property
    def success_count(self) -> int:
        return sum(1 for item in self.command_results if item.ok)


def collect_routeros_data(
    client: CommandRunner,
    exports_dir: Path,
    timestamp: datetime | None = None,
    logger: logging.Logger | None = None,
) -> CollectionResult:
    try:
        validate_all_commands()
    except Exception as exc:
        raise CollectionError("Allowlist de comandos invalida.") from exc

    collected_at = timestamp or datetime.now()
    exports_dir.mkdir(parents=True, exist_ok=True)
    command_results: list[CommandResult] = []

    sections: list[str] = []
    for command in READ_ONLY_COMMANDS:
        if logger:
            safe_log(logger, logging.INFO, "Executando comando read-only: %s", command)
        try:
            output = client.run_command(command)
            sanitized_output = sanitize_text(output)
            command_results.append(CommandResult(command=command, output=sanitized_output))
            sections.append(f"=== COMMAND: {command} ===\n{sanitized_output.strip()}\n")
            if logger:
                safe_log(logger, logging.INFO, "Comando concluido: %s", command)
        except Exception as exc:
            sanitized_error = sanitize_text(str(exc))
            command_results.append(
                CommandResult(command=command, output="", ok=False, error=sanitized_error)
            )
            sections.append(
                f"=== COMMAND: {command} ===\n[ERROR] {sanitized_error.strip()}\n"
            )
            if logger:
                safe_log(
                    logger,
                    logging.ERROR,
                    "Comando falhou: %s | %s",
                    command,
                    sanitized_error,
                )

    filename = f"{collected_at:%Y-%m-%d_%H%M%S}_routeros_collect_sanitized.txt"
    export_path = exports_dir / filename
    export_path.write_text("\n".join(sections), encoding="utf-8")

    return CollectionResult(
        timestamp=collected_at,
        export_path=export_path,
        command_results=command_results,
    )


def dry_run_commands() -> tuple[str, ...]:
    validate_all_commands()
    return READ_ONLY_COMMANDS
