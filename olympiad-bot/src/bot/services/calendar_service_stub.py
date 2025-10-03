"""Заглушка сервиса синхронизации с календарём."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from uuid import uuid4

from bot.utils.logging import logger


@dataclass(slots=True)
class CalendarServiceStub:
    """Простейшая заглушка календарного сервиса."""

    def generate_unique_link(self, tg_user_id: int) -> str:
        """Вернуть фиктивную ссылку синхронизации и залогировать обращение."""

        unique_link = f"https://calendar.stub/sync/{uuid4()}"
        logger.info(
            "Generated calendar sync link for user {user_id}: {link}",
            user_id=tg_user_id,
            link=unique_link,
        )
        return unique_link

    def confirm_synchronization(self, tg_user_id: int) -> None:
        """Залогировать подтверждение синхронизации."""

        logger.info(
            "User {user_id} confirmed calendar synchronization (stub)",
            user_id=tg_user_id,
        )


@lru_cache
def get_calendar_service() -> CalendarServiceStub:
    """Вернуть синглтон заглушки календарного сервиса."""

    return CalendarServiceStub()


__all__ = ["CalendarServiceStub", "get_calendar_service"]
