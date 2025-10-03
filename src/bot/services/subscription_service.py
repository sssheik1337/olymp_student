"""Заглушечный сервис управления подпиской."""

from __future__ import annotations

from functools import lru_cache
from typing import Callable
from uuid import uuid4

from bot.utils.logging import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_config
from bot.repository.db import AsyncSessionLocal
from bot.repository.models import User

SessionFactory = Callable[[], AsyncSession]


class SubscriptionService:
    """Управление подпиской пользователя в режиме заглушки."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory = session_factory or AsyncSessionLocal
        settings = get_config()
        self._provider = settings.pay_provider
        self._return_url = settings.pay_return_url

    async def is_subscribed(self, *, tg_user_id: int) -> bool:
        """Проверить статус подписки пользователя."""

        async with self._session_factory() as session:
            result = await session.execute(select(User.is_subscribed).where(User.tg_id == tg_user_id))
            value = result.scalar_one_or_none()
            return bool(value)

    async def create_payment_link(self, *, tg_user_id: int, username: str | None = None) -> str:
        """Сгенерировать фиктивную ссылку на оплату и сохранить профиль пользователя."""

        async with self._session_factory() as session:
            async with session.begin():
                await self._get_or_create_user(session, tg_user_id, username)

        token = uuid4().hex
        link = f"https://pay.{self._provider}/invoice/{token}?return={self._return_url}"
        logger.info(
            "Выдана заглушечная ссылка на оплату подписки",
            extra={"tg_user_id": tg_user_id, "payment_link": link},
        )
        return link

    async def activate_subscription(self, *, tg_user_id: int, username: str | None = None) -> None:
        """Отметить пользователя как оформившего подписку."""

        async with self._session_factory() as session:
            async with session.begin():
                user = await self._get_or_create_user(session, tg_user_id, username)
                if not user.is_subscribed:
                    user.is_subscribed = True
                    await session.flush()

        logger.info("Подписка активирована", extra={"tg_user_id": tg_user_id})

    async def _get_or_create_user(
        self, session: AsyncSession, tg_user_id: int, username: str | None
    ) -> User:
        """Найти пользователя по Telegram ID или создать запись."""

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


@lru_cache
def get_subscription_service() -> SubscriptionService:
    """Получить singleton-сервис подписки."""

    return SubscriptionService()


__all__ = ["SubscriptionService", "get_subscription_service"]
