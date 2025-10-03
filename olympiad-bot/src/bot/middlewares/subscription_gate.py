"""Middleware для проверки подписки пользователя."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.config import get_config
from bot.services.subscription_service import get_subscription_service
from bot.utils import texts

ALLOWED_COMMANDS = {"/start", "/help", "/subscription"}
ALLOWED_CALLBACK_PREFIXES = ("subscription:", "menu:subscription", "menu:help")


class SubscriptionGateMiddleware(BaseMiddleware):
    """Блокирует доступ к функциональности без активной подписки."""

    def __init__(self) -> None:
        super().__init__()
        self._subscription_service = get_subscription_service()
        settings = get_config()
        self._admin_ids = set(settings.admin_ids)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            if self._is_allowed_message(event):
                return await handler(event, data)
            if await self._has_access(event.from_user):
                return await handler(event, data)
            await event.answer(texts.SUBSCRIPTION_REQUIRED_MESSAGE)
            return None

        if isinstance(event, CallbackQuery):
            if self._is_allowed_callback(event):
                return await handler(event, data)
            if await self._has_access(event.from_user):
                return await handler(event, data)
            await event.answer(texts.SUBSCRIPTION_REQUIRED_MESSAGE, show_alert=True)
            message = event.message
            if message is not None:
                await message.answer(texts.SUBSCRIPTION_REQUIRED_MESSAGE)
            return None

        return await handler(event, data)

    def _is_allowed_message(self, message: Message) -> bool:
        if message.from_user and message.from_user.id in self._admin_ids:
            return True
        text = (message.text or message.caption or "").strip()
        if not text.startswith("/"):
            return False
        command = text.split()[0].split("@", 1)[0].lower()
        return command in ALLOWED_COMMANDS

    def _is_allowed_callback(self, callback: CallbackQuery) -> bool:
        user = callback.from_user
        if user and user.id in self._admin_ids:
            return True
        payload = callback.data or ""
        return any(payload.startswith(prefix) for prefix in ALLOWED_CALLBACK_PREFIXES)

    async def _has_access(self, user: Any) -> bool:
        if user is None:
            return False
        if user.id in self._admin_ids:
            return True
        return await self._subscription_service.is_subscribed(tg_user_id=user.id)


__all__ = ["SubscriptionGateMiddleware"]
