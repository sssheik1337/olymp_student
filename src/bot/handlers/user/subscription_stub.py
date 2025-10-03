"""Маршрутизатор заглушки подписки."""

from __future__ import annotations

from typing import Iterable

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.subscription import (
    BACK_TO_SUBSCRIPTION_CALLBACK,
    CONFIRM_CALLBACK,
    PAY_CALLBACK,
    build_subscription_overview_keyboard,
    build_subscription_payment_keyboard,
)
from bot.services.subscription_service import get_subscription_service
from bot.utils import texts

router = Router(name="user_subscription_stub")


def _join_lines(lines: Iterable[str], *, link: str | None = None) -> str:
    prepared: list[str] = []
    for line in lines:
        prepared.append(line.format(link=link) if link is not None else line)
    return "\n".join(prepared)


async def _show_subscription_overview(
    message: Message,
    *,
    tg_user_id: int,
    username: str | None,
    edit: bool,
) -> None:
    service = get_subscription_service()
    is_subscribed = await service.is_subscribed(tg_user_id=tg_user_id)
    text_lines = (
        texts.SUBSCRIPTION_ACTIVE_LINES if is_subscribed else texts.SUBSCRIPTION_INTRO_LINES
    )
    text = _join_lines(text_lines)
    keyboard = build_subscription_overview_keyboard(is_subscribed=is_subscribed)

    if edit:
        try:
            await message.edit_text(text, reply_markup=keyboard)
            return
        except TelegramBadRequest:
            pass
    await message.answer(text, reply_markup=keyboard)


@router.message(Command("subscription"))
async def handle_subscription_command(message: Message) -> None:
    """Открыть раздел подписки по команде."""

    user = message.from_user
    if user is None:
        return
    await _show_subscription_overview(
        message,
        tg_user_id=user.id,
        username=user.username,
        edit=False,
    )


@router.callback_query(F.data == BACK_TO_SUBSCRIPTION_CALLBACK)
async def open_subscription_from_menu(callback: CallbackQuery) -> None:
    """Показать раздел подписки из меню или кнопки возврата."""

    await callback.answer()
    message = callback.message
    user = callback.from_user
    if message is None or user is None:
        return
    await _show_subscription_overview(
        message,
        tg_user_id=user.id,
        username=user.username,
        edit=True,
    )


@router.callback_query(F.data == PAY_CALLBACK)
async def handle_subscription_checkout(callback: CallbackQuery) -> None:
    """Сгенерировать заглушечную ссылку на оплату подписки."""

    user = callback.from_user
    message = callback.message
    if user is None or message is None:
        await callback.answer("Команда доступна только в чате", show_alert=True)
        return

    service = get_subscription_service()
    payment_link = await service.create_payment_link(
        tg_user_id=user.id,
        username=user.username,
    )
    text = _join_lines(texts.SUBSCRIPTION_PAYMENT_PROMPT_LINES, link=payment_link)
    keyboard = build_subscription_payment_keyboard()

    await callback.answer("Ссылка на оплату готова")
    try:
        await message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == CONFIRM_CALLBACK)
async def handle_subscription_confirm(callback: CallbackQuery) -> None:
    """Подтвердить оплату и активировать подписку."""

    user = callback.from_user
    message = callback.message
    if user is None or message is None:
        await callback.answer("Команда доступна только в чате", show_alert=True)
        return

    service = get_subscription_service()
    await service.activate_subscription(
        tg_user_id=user.id,
        username=user.username,
    )

    confirmation = _join_lines(texts.SUBSCRIPTION_CONFIRMED_LINES)
    keyboard = build_subscription_overview_keyboard(is_subscribed=True)

    await callback.answer("Подписка активирована ✨")
    try:
        await message.edit_text(confirmation, reply_markup=keyboard)
    except TelegramBadRequest:
        await message.answer(confirmation, reply_markup=keyboard)


__all__ = ["router"]
