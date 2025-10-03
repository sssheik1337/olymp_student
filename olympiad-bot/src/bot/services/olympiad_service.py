"""Сервис работы с каталогом олимпиад и избранным."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from functools import lru_cache
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repository.db import AsyncSessionLocal
from bot.repository.models import Olympiad, User, UserOlympiad
from bot.services.reminder_service import get_reminder_service


@dataclass(frozen=True, slots=True)
class Subject:
    """Описание учебного предмета."""

    code: str
    title: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class OlympiadInfo:
    """Демо-описание олимпиады для каталога."""

    id: int
    subject_code: str
    title: str
    reg_deadline: date | None = None
    round_date: date | None = None
    description: str | None = None


DEMO_SUBJECTS: tuple[Subject, ...] = (
    Subject(code="math", title="Математика"),
    Subject(code="informatics", title="Информатика"),
    Subject(code="physics", title="Физика"),
)


DEMO_OLYMPIADS: tuple[OlympiadInfo, ...] = (
    OlympiadInfo(
        id=1,
        subject_code="math",
        title="Олимпиада НИУ ВШЭ по математике",
        reg_deadline=date(2024, 10, 1),
        round_date=date(2024, 11, 10),
        description="Первая и заключительная отборочные площадки НИУ ВШЭ.",
    ),
    OlympiadInfo(
        id=2,
        subject_code="math",
        title="ВсОШ. Теоретический тур",
        reg_deadline=date(2024, 9, 20),
        round_date=date(2024, 12, 5),
        description="Муниципальный этап Всероссийской олимпиады школьников.",
    ),
    OlympiadInfo(
        id=3,
        subject_code="informatics",
        title="Олимпиада НТИ. Профиль "
        "Информационные технологии",
        reg_deadline=date(2024, 9, 15),
        round_date=date(2024, 11, 25),
        description="Командные задачи на алгоритмы и программирование.",
    ),
    OlympiadInfo(
        id=4,
        subject_code="informatics",
        title="ВсОШ по информатике",
        reg_deadline=date(2024, 9, 30),
        round_date=date(2024, 12, 12),
        description="Муниципальный и региональный этапы Всероса.",
    ),
    OlympiadInfo(
        id=5,
        subject_code="physics",
        title="Физтех. Олимпиада Физтеха",
        reg_deadline=date(2024, 10, 5),
        round_date=date(2024, 11, 30),
        description="Очный тур в кампусе МФТИ и онлайн-формат.",
    ),
    OlympiadInfo(
        id=6,
        subject_code="physics",
        title="Ломоносов по физике",
        reg_deadline=date(2024, 9, 28),
        round_date=date(2024, 10, 18),
        description="Олимпиада МГУ имени М. В. Ломоносова.",
    ),
)


class OlympiadService:
    """Бизнес-логика каталога олимпиад и избранного."""

    def __init__(self, session_factory: type[AsyncSession] | None = None) -> None:
        self._session_factory = session_factory or AsyncSessionLocal
        self._subjects: dict[str, Subject] = {item.code: item for item in DEMO_SUBJECTS}
        self._subjects_order: tuple[Subject, ...] = tuple(
            sorted(self._subjects.values(), key=lambda subject: subject.title.lower())
        )
        self._olympiads_by_subject: dict[str, list[OlympiadInfo]] = {}
        self._olympiads_by_id: dict[int, OlympiadInfo] = {}
        for olympiad in DEMO_OLYMPIADS:
            self._olympiads_by_subject.setdefault(olympiad.subject_code, []).append(olympiad)
            self._olympiads_by_id[olympiad.id] = olympiad
        for values in self._olympiads_by_subject.values():
            values.sort(key=lambda olymp: olymp.title.lower())

    def list_subjects(self) -> Sequence[Subject]:
        """Вернуть все учебные предметы в алфавитном порядке."""

        return self._subjects_order

    def get_subject(self, code: str) -> Subject | None:
        """Получить описание предмета по его коду."""

        return self._subjects.get(code)

    def list_olympiads(self, subject_code: str) -> Sequence[OlympiadInfo]:
        """Вернуть олимпиады для выбранного предмета."""

        return tuple(self._olympiads_by_subject.get(subject_code, ()))

    def get_olympiad(self, olympiad_id: int) -> OlympiadInfo | None:
        """Получить описание олимпиады из демо-каталога."""

        return self._olympiads_by_id.get(olympiad_id)

    async def add_to_favorites(
        self, *,
        tg_user_id: int,
        olympiad_id: int,
        username: str | None = None,
    ) -> bool:
        """Добавить олимпиаду в избранное пользователя.

        Возвращает ``True``, если запись была создана, и ``False`` в случае,
        когда олимпиада уже находится в избранном.
        """

        olympiad_info = self.get_olympiad(olympiad_id)
        if olympiad_info is None:
            raise ValueError("Unknown olympiad identifier")

        reminder_service = get_reminder_service()

        async with self._session_factory() as session:
            async with session.begin():
                user = await self._get_or_create_user(session, tg_user_id, username)
                await self._ensure_demo_olympiad(session, olympiad_info)

                existing = await session.get(UserOlympiad, (user.id, olympiad_id))
                if existing is not None:
                    return False

                session.add(
                    UserOlympiad(
                        user_id=user.id,
                        olympiad_id=olympiad_id,
                        created_at=datetime.now(tz=timezone.utc),
                    )
                )

                await reminder_service.schedule_for_favorite(
                    session=session,
                    user_id=user.id,
                    olympiad_id=olympiad_id,
                    reg_deadline=olympiad_info.reg_deadline,
                    round_date=olympiad_info.round_date,
                )

            return True

    async def _get_or_create_user(
        self, session: AsyncSession, tg_user_id: int, username: str | None
    ) -> User:
        """Найти пользователя по Telegram ID или создать нового."""

        result = await session.execute(select(User).where(User.tg_id == tg_user_id))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(tg_id=tg_user_id, username=username)
            session.add(user)
            await session.flush()
            return user

        if username and user.username != username:
            user.username = username
            await session.flush()
        return user

    async def _ensure_demo_olympiad(
        self, session: AsyncSession, olympiad_info: OlympiadInfo
    ) -> None:
        """Убедиться, что демо-олимпиада сохранена в базе."""

        db_olympiad = await session.get(Olympiad, olympiad_info.id)
        if db_olympiad is not None:
            return

        subject = self.get_subject(olympiad_info.subject_code)
        session.add(
            Olympiad(
                id=olympiad_info.id,
                subject=subject.title if subject else olympiad_info.subject_code,
                title=olympiad_info.title,
                reg_deadline=olympiad_info.reg_deadline,
                round_date=olympiad_info.round_date,
                description=olympiad_info.description,
            )
        )
        await session.flush()


@lru_cache
def get_olympiad_service() -> OlympiadService:
    """Получить singleton-сервис каталога олимпиад."""

    return OlympiadService()


__all__ = [
    "OlympiadInfo",
    "OlympiadService",
    "Subject",
    "get_olympiad_service",
]
