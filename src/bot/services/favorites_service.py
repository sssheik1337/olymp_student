"""Сервис для работы с избранными олимпиадами."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repository.db import AsyncSessionLocal
from bot.repository.models import Olympiad, User, UserOlympiad


@dataclass(frozen=True, slots=True)
class FavoriteOlympiad:
    """Представление избранной олимпиады пользователя."""

    olympiad_id: int
    title: str
    subject: str
    reg_deadline: date | None
    round_date: date | None
    description: str | None
    added_at: datetime


class FavoritesService:
    """Бизнес-логика для списка избранных олимпиад."""

    def __init__(self, session_factory: type[AsyncSession] | None = None) -> None:
        self._session_factory = session_factory or AsyncSessionLocal

    async def list_favorites(self, *, tg_user_id: int) -> Sequence[FavoriteOlympiad]:
        """Вернуть все избранные олимпиады пользователя."""

        async with self._session_factory() as session:
            stmt = (
                select(UserOlympiad, Olympiad)
                .join(User, User.id == UserOlympiad.user_id)
                .join(Olympiad, Olympiad.id == UserOlympiad.olympiad_id)
                .where(User.tg_id == tg_user_id)
                .order_by(UserOlympiad.created_at.desc())
            )
            result = await session.execute(stmt)
            favorites: list[FavoriteOlympiad] = []
            for user_olympiad, olympiad in result.all():
                favorites.append(
                    FavoriteOlympiad(
                        olympiad_id=olympiad.id,
                        title=olympiad.title,
                        subject=olympiad.subject,
                        reg_deadline=olympiad.reg_deadline,
                        round_date=olympiad.round_date,
                        description=olympiad.description,
                        added_at=user_olympiad.created_at,
                    )
                )
            return tuple(favorites)

    async def remove_favorite(self, *, tg_user_id: int, olympiad_id: int) -> bool:
        """Удалить олимпиаду из избранного пользователя."""

        async with self._session_factory() as session:
            async with session.begin():
                user_id = await self._get_user_id(session, tg_user_id)
                if user_id is None:
                    return False

                favorite = await session.get(UserOlympiad, (user_id, olympiad_id))
                if favorite is None:
                    return False

                await session.delete(favorite)

            return True

    async def _get_user_id(self, session: AsyncSession, tg_user_id: int) -> int | None:
        """Получить внутренний идентификатор пользователя."""

        result = await session.execute(
            select(User.id).where(User.tg_id == tg_user_id)
        )
        return result.scalar_one_or_none()


@lru_cache
def get_favorites_service() -> FavoritesService:
    """Получить singleton-сервис избранных олимпиад."""

    return FavoritesService()


__all__ = [
    "FavoriteOlympiad",
    "FavoritesService",
    "get_favorites_service",
]
