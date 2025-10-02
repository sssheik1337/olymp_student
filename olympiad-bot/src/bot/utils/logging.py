"""Logging utilities using loguru."""

from loguru import logger


def setup_logging() -> None:
    """Configure the loguru logger."""
    logger.info("Logging is not configured yet")
