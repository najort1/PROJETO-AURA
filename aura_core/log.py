"""Logging padronizado: console + arquivo logs/aura.log."""
from __future__ import annotations

import logging
import sys

from aura_core.config import settings
from aura_core.paths import ensure_dir

_configured = False


def get_logger(name: str) -> logging.Logger:
    global _configured
    if not _configured:
        ensure_dir("logs")
        level = getattr(logging, str(settings().get("logging", {}).get("level", "INFO")).upper())
        fmt = "%(asctime)s %(levelname)-7s %(name)s :: %(message)s"
        handlers = [
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(ensure_dir("logs") / "aura.log", encoding="utf-8"),
        ]
        logging.basicConfig(level=level, format=fmt, handlers=handlers)
        _configured = True
    return logging.getLogger(name)
