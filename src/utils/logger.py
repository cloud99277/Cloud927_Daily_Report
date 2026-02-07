"""Logger module with rotating file support."""

import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler


def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with date-based rotation.

    Args:
        name: Name of the logger.

    Returns:
        Configured logger instance.
    """
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    log_file = os.path.join(logs_dir, 'app.log')

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    handler = TimedRotatingFileHandler(log_file, when='midnight', backupCount=7)
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    logger.addHandler(handler)

    return logger
