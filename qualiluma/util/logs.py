from __future__ import annotations

import sys

import loguru
from loguru import logger


def init_logging(
    log_file: str, file_log_level: str = "DEBUG", console_log_level: str = "INFO"
) -> None:
    """Set logging configuration.

    Args:
        log_file (str): Path to the log file.
        file_log_level (str): Logging level for the file.
        console_log_level (str): Logging level for the console.
    """
    logger.remove()  # Remove default logger
    logger.add(log_file, level=file_log_level)
    logger.add(sys.stdout, level=console_log_level)


def get_logger(name: str) -> loguru.Logger:
    """Get a logger with the specified name.

    Args:
        name (str): Name of the logger.

    Returns:
        loguru.Logger: A logger instance.
    """
    return logger.bind(name=name)
