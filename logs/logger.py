"""
Centralized logging configuration for StockStream.
Industry-standard structured logging with rotation support.
"""
import logging
import os
from pathlib import Path


def setup_logger(name: str, log_file: str = "app.log", level: int = logging.INFO) -> logging.Logger:
    """
    Create and configure a logger with file and optionally console output.

    Args:
        name: Logger name (typically __name__)
        log_file: Log filename (relative to logs/ directory)
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    logs_dir = Path(__file__).parent
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / log_file
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
