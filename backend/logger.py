"""
Centralized logging configuration for the SEO AI Agent backend.

Usage:
    from logger import get_logger
    log = get_logger(__name__)
    log.info("Audit started", extra={"audit_id": 42, "url": "https://example.com"})
"""
import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)

_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Track configured loggers to avoid duplicate handlers
_configured: set[str] = set()


def get_logger(name: str) -> logging.Logger:
    """Return a logger with console + rotating-file handlers."""
    logger = logging.getLogger(name)

    if name in _configured:
        return logger

    _configured.add(name)
    logger.setLevel(_LOG_LEVEL)
    logger.propagate = False  # Don't bubble up to root logger

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(_FORMATTER)
    logger.addHandler(console_handler)

    # Rotating file handler — 10 MB max, keep 5 backups
    file_handler = RotatingFileHandler(
        filename=os.path.join(_LOG_DIR, "app.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(_FORMATTER)
    logger.addHandler(file_handler)

    return logger
