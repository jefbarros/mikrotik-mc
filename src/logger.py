from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from .paths import LOGS_DIR
from .sanitizer import sanitize_text


def setup_logger() -> logging.Logger:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("mikrotik_ai_automation")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_path = LOGS_DIR / f"{datetime.now():%Y-%m-%d}_mikrotik_ai.log"
    if not _has_file_handler(logger, log_path):
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        logger.addHandler(handler)

    return logger


def safe_log(logger: logging.Logger, level: int, message: str, *args: object) -> None:
    if args:
        message = message % tuple(sanitize_text(str(arg)) for arg in args)
    logger.log(level, sanitize_text(message))


def _has_file_handler(logger: logging.Logger, log_path: Path) -> bool:
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            if Path(handler.baseFilename) == log_path:
                return True
    return False

