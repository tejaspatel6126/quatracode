"""
Centralized logging configuration.
Sets up structured logging with timestamp, level, module, and request ID support.
Never logs passwords, API keys, tokens, or credentials.
"""

import logging
import sys
from typing import Optional

from app.core.config import get_settings


class RequestIdFilter(logging.Filter):
    """Inject request_id into log records when available."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def setup_logging() -> None:
    """Configure the root logger for the application."""
    settings = get_settings()
    log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)

    fmt = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "req=%(request_id)s | %(message)s"
    )
    formatter = logging.Formatter(fmt, datefmt="%Y-%m-%dT%H:%M:%S")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers on reloads (uvicorn --reload)
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers.clear()
        root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger by name."""
    return logging.getLogger(name)
