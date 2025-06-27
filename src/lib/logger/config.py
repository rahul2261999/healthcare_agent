"""
Logger configuration settings.
"""

import sys
import os
from pathlib import Path
from datetime import timedelta

# Log directory configuration
LOGS_DIR = Path("src/logs")

# Console logging format
CONSOLE_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# File logging format
FILE_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"

# Log rotation settings
ROTATION_INTERVAL = timedelta(days=2)
RETENTION_PERIOD = timedelta(days=2)

# Log levels from environment variables with defaults
CONSOLE_LEVEL = os.getenv("LOG_CONSOLE_LEVEL", "INFO").upper()
FILE_LEVEL = os.getenv("LOG_FILE_LEVEL", "DEBUG").upper()

# Validate log levels
VALID_LOG_LEVELS = {"TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"}
if CONSOLE_LEVEL not in VALID_LOG_LEVELS:
    print(f"Warning: Invalid LOG_CONSOLE_LEVEL '{CONSOLE_LEVEL}'. Using default 'INFO'")
    CONSOLE_LEVEL = "INFO"

if FILE_LEVEL not in VALID_LOG_LEVELS:
    print(f"Warning: Invalid LOG_FILE_LEVEL '{FILE_LEVEL}'. Using default 'DEBUG'")
    FILE_LEVEL = "DEBUG"

# Log file name format
LOG_FILE_FORMAT = "app_{time:YYYY-MM-DD}.log" 