"""
lib/logger.py — Structured logging for the Instagram Engine.

Writes both to console and daily log files under logs/.
Each call is timestamped in IST.

Usage:
    from lib.logger import EngineLogger
    log = EngineLogger()
    log.info("Content generated")
    log.error("API call failed", extra={"status_code": 500})
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

from lib.utils import LOGS_DIR, ensure_dirs

IST = timezone(timedelta(hours=5, minutes=30))


class EngineLogger:
    """Dual-output logger: console + daily file."""

    def __init__(self, name: str = "instagram_engine"):
        ensure_dirs()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers on re-import
        if self.logger.handlers:
            self.logger.handlers.clear()

        # ── Console handler ───────────────────────────────────────────────────
        console_fmt = logging.Formatter(
            "%(asctime)s │ %(levelname)-7s │ %(message)s",
            datefmt="%H:%M:%S",
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_fmt)
        self.logger.addHandler(console_handler)

        # ── File handler (one file per day) ───────────────────────────────────
        today = datetime.now(IST).strftime("%Y-%m-%d")
        log_file: Path = LOGS_DIR / f"engine_{today}.log"
        file_fmt = logging.Formatter(
            "%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_fmt)
        self.logger.addHandler(file_handler)

    # ── Public methods ─────────────────────────────────────────────────────────

    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, kwargs)

    def warn(self, message: str, **kwargs):
        self._log(logging.WARNING, message, kwargs)

    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, kwargs)

    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, kwargs)

    def section(self, message: str):
        divider = "=" * 60
        self.logger.info(divider)
        self.logger.info(f"  {message}")
        self.logger.info(divider)

    # ── Internal ───────────────────────────────────────────────────────────────

    def _log(self, level: int, message: str, extra: dict):
        detail = ""
        if extra:
            detail = " │ " + " | ".join(f"{k}={v}" for k, v in extra.items())
        self.logger.log(level, f"{message}{detail}")
