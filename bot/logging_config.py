"""
logging_config.py - Structured logging setup for the trading bot.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")

_configured = False


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Configure and return the root logger with both file and console handlers.
    File handler: DEBUG and above (full detail for audit trail).
    Console handler: INFO and above (clean UX).
    """
    global _configured
    if _configured:
        return logging.getLogger("trading_bot")

    os.makedirs(LOG_DIR, exist_ok=True)

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # --- File handler (rotating, keeps last 5 × 2 MB) ---
    fh = RotatingFileHandler(LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # --- Console handler ---
    ch = logging.StreamHandler()
    ch.setLevel(numeric_level)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.propagate = False

    _configured = True
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the trading_bot namespace."""
    return logging.getLogger(f"trading_bot.{name}")
