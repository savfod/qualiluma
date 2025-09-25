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

    def filter_simplified(record):
        return record["extra"].get("logger_type") == "results"

    def filter_default(record):
        return record["extra"].get("logger_type") not in ["results"]

    logger.add(log_file, level=file_log_level, filter=filter_default)
    logger.add(sys.stdout, level=console_log_level, filter=filter_default)

    logger.add(
        log_file,
        format="...:<cyan>{line}</cyan> | <level>{level: <8}</level> | {message}",
        filter=filter_simplified,
        level=file_log_level,
    )
    logger.add(
        sys.stdout,
        format="{message}",
        filter=filter_simplified,
        level=console_log_level,
    )


def get_logger(name: str, results_mode: bool = False) -> loguru.Logger:
    """Get a logger with the specified name.

    Args:
        name (str): Name of the logger.
        results_mode (bool): Whether to use a simplified results log format.

    Returns:
        loguru.Logger: A logger instance.
    """
    return logger.bind(name=name, logger_type="results" if results_mode else "default")
