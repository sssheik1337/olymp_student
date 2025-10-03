"""Планировщик фоновых задач для напоминаний."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from bot.utils.logging import logger
from sqlalchemy import select

from bot.repository.db import AsyncSessionLocal
from bot.repository.models import Reminder


_REMINDER_JOB_ID = "reminders:dispatch"
_SCHEDULER: AsyncIOScheduler | None = None


async def _process_due_reminders() -> None:
    """Асинхронно обработать просроченные напоминания."""

    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                select(Reminder).where(
                    Reminder.sent_at.is_(None),
                    Reminder.scheduled_at <= now,
                )
            )
            reminders = result.scalars().all()
            if not reminders:
                return

            for reminder in reminders:
                logger.info(
                    "Отправляем напоминание %s для пользователя %s по олимпиаде %s",
                    reminder.kind.value,
                    reminder.user_id,
                    reminder.olympiad_id,
                )
                reminder.sent_at = now


def start_scheduler() -> AsyncIOScheduler:
    """Создать и запустить планировщик напоминаний."""

    global _SCHEDULER

    if _SCHEDULER and _SCHEDULER.running:
        return _SCHEDULER

    loop = asyncio.get_running_loop()

    scheduler = AsyncIOScheduler(timezone=timezone.utc, event_loop=loop)
    scheduler.add_job(
        _process_due_reminders,
        trigger=IntervalTrigger(minutes=1),
        id=_REMINDER_JOB_ID,
        max_instances=1,
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Фоновый планировщик напоминаний запущен")

    _SCHEDULER = scheduler
    return scheduler


def shutdown_scheduler() -> None:
    """Остановить планировщик напоминаний."""

    global _SCHEDULER

    if _SCHEDULER is None:
        return

    _SCHEDULER.shutdown(wait=False)
    _SCHEDULER = None
    logger.info("Фоновый планировщик напоминаний остановлен")


__all__ = [
    "start_scheduler",
    "shutdown_scheduler",
]
