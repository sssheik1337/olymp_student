"""Утилиты для настройки логирования с помощью loguru."""

from __future__ import annotations

import sys
from typing import Final

from loguru import logger as _logger

DEFAULT_LOG_FORMAT: Final[str] = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def setup_logging(*, level: str = "INFO") -> None:
    """Настроить глобальный логгер loguru."""

    _logger.remove()
    _logger.add(
        sys.stdout,
        level=level.upper(),
        format=DEFAULT_LOG_FORMAT,
        backtrace=True,
        diagnose=False,
        enqueue=True,
    )


logger = _logger

__all__ = ["setup_logging", "logger"]
