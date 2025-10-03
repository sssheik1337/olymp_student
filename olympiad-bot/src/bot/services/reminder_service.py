"""Сервис генерации напоминаний для олимпиад."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from typing import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repository.db import AsyncSessionLocal
from bot.repository.models import Reminder, ReminderKind


@dataclass(frozen=True, slots=True)
class ReminderPlan:
    """Описание напоминания, подлежащего созданию."""

    kind: ReminderKind
    scheduled_at: datetime


class ReminderService:
    """Логика формирования напоминаний при работе с избранным."""

    def __init__(self, session_factory: type[AsyncSession] | None = None) -> None:
        self._session_factory = session_factory or AsyncSessionLocal

    async def schedule_for_favorite(
        self,
        *,
        user_id: int,
        olympiad_id: int,
        reg_deadline: date | None,
        round_date: date | None,
        session: AsyncSession | None = None,
    ) -> int:
        """Создать напоминания при добавлении олимпиады в избранное.

        Возвращает количество новых напоминаний. Если даты недоступны или
        соответствующие напоминания уже существуют, записи не создаются.
        """

        owns_session = session is None
        if owns_session:
            async with self._session_factory() as new_session:
                async with new_session.begin():
                    return await self._schedule(
                        session=new_session,
                        user_id=user_id,
                        olympiad_id=olympiad_id,
                        reg_deadline=reg_deadline,
                        round_date=round_date,
                    )
        return await self._schedule(
            session=session,
            user_id=user_id,
            olympiad_id=olympiad_id,
            reg_deadline=reg_deadline,
            round_date=round_date,
        )

    async def _schedule(
        self,
        *,
        session: AsyncSession,
        user_id: int,
        olympiad_id: int,
        reg_deadline: date | None,
        round_date: date | None,
    ) -> int:
        plans = tuple(self._build_plans(reg_deadline=reg_deadline, round_date=round_date))
        if not plans:
            return 0

        existing_stmt = select(Reminder.kind).where(
            Reminder.user_id == user_id,
            Reminder.olympiad_id == olympiad_id,
            Reminder.kind.in_([plan.kind for plan in plans]),
        )
        existing_result = await session.execute(existing_stmt)
        existing_kinds = set(existing_result.scalars().all())

        created = 0
        for plan in plans:
            if plan.kind in existing_kinds:
                continue
            reminder = Reminder(
                user_id=user_id,
                olympiad_id=olympiad_id,
                kind=plan.kind,
                scheduled_at=plan.scheduled_at,
            )
            session.add(reminder)
            created += 1
        return created

    def _build_plans(
        self,
        *,
        reg_deadline: date | None,
        round_date: date | None,
    ) -> Iterable[ReminderPlan]:
        now = datetime.now(timezone.utc)
        reminder_time = time(hour=9, minute=0, tzinfo=timezone.utc)

        def to_datetime(target_date: date) -> datetime:
            return datetime.combine(target_date, reminder_time)

        if reg_deadline:
            week_before = reg_deadline - timedelta(days=7)
            if week_before >= now.date():
                scheduled = to_datetime(week_before)
                if scheduled >= now:
                    yield ReminderPlan(ReminderKind.REG_WEEK, scheduled)

        if round_date:
            day_before = round_date - timedelta(days=1)
            if day_before >= now.date():
                scheduled = to_datetime(day_before)
                if scheduled >= now:
                    yield ReminderPlan(ReminderKind.DAY_BEFORE, scheduled)

            if round_date >= now.date():
                scheduled = to_datetime(round_date)
                if scheduled >= now:
                    yield ReminderPlan(ReminderKind.DAY_OF, scheduled)


@lru_cache
def get_reminder_service() -> ReminderService:
    """Получить singleton-сервис напоминаний."""

    return ReminderService()


__all__: Sequence[str] = [
    "ReminderPlan",
    "ReminderService",
    "get_reminder_service",
]
