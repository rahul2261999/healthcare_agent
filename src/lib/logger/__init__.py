"""
Logger package for the application.
Provides a configured loguru instance for logging.
"""

from .config import (
    LOGS_DIR,
    CONSOLE_FORMAT,
    FILE_FORMAT,
    ROTATION_INTERVAL,
    RETENTION_PERIOD,
    CONSOLE_LEVEL,
    FILE_LEVEL,
    LOG_FILE_FORMAT,
)
from loguru import logger
import sys

# Create logs directory if it doesn't exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure loguru logger
logger.remove()  # Remove default handler

# Add console handler with colors
logger.add(
    sys.stderr,
    format=CONSOLE_FORMAT,
    level=CONSOLE_LEVEL,
    colorize=True
)

# Add file handler with rotation
logger.add(
    LOGS_DIR / LOG_FILE_FORMAT,
    rotation=ROTATION_INTERVAL,
    retention=RETENTION_PERIOD,
    format=FILE_FORMAT,
    level=FILE_LEVEL,
    encoding="utf-8"
)

__all__ = ["logger"] 