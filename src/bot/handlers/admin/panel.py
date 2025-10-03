"""Маршрутизатор административной панели."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.config import get_config
from bot.keyboards.admin_menu import (
    ADMIN_BACK_CALLBACK,
    ADMIN_OLYMPIADS_CALLBACK,
    ADMIN_REMINDERS_CALLBACK,
    build_admin_menu_keyboard,
)

router = Router(name="admin_panel")

_SETTINGS = get_config()
_ADMIN_IDS = set(_SETTINGS.admin_ids)


def _is_admin(user_id: int | None) -> bool:
    return user_id is not None and user_id in _ADMIN_IDS


async def _show_panel(message: Message, *, edit: bool = False) -> None:
    keyboard = build_admin_menu_keyboard()
    text = (
        "Админ-панель. Выберите раздел для управления ботом."
        "\nДоступны материалы, олимпиады и напоминания."
    )
    if edit:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)


@router.message(Command("admin"))
async def open_admin_panel(message: Message) -> None:
    """Открыть панель администратора."""

    user = message.from_user
    if not _is_admin(user.id if user else None):
        await message.answer("Команда доступна только администраторам.")
        return

    await _show_panel(message, edit=False)


@router.callback_query(F.data == ADMIN_BACK_CALLBACK)
async def return_to_admin_menu(callback: CallbackQuery) -> None:
    """Вернуться к списку разделов админ-панели."""

    user = callback.from_user
    if not _is_admin(user.id if user else None):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    message = callback.message
    if message is None:
        await callback.answer()
        return

    await callback.answer()
    await _show_panel(message, edit=True)


@router.callback_query(F.data == ADMIN_OLYMPIADS_CALLBACK)
async def handle_olympiads_stub(callback: CallbackQuery) -> None:
    """Пока что выводит заглушку для управления олимпиадами."""

    user = callback.from_user
    if not _is_admin(user.id if user else None):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    await callback.answer()
    message = callback.message
    if message is not None:
        await message.answer(
            "Раздел управления олимпиадами появится позднее."
            " Сейчас доступно управление материалами и просмотр напоминаний."
        )


@router.callback_query(F.data == ADMIN_REMINDERS_CALLBACK)
async def handle_reminders_stub(callback: CallbackQuery) -> None:
    """Пока что выводит заглушку для управления напоминаниями."""

    user = callback.from_user
    if not _is_admin(user.id if user else None):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    await callback.answer()
    message = callback.message
    if message is not None:
        await message.answer(
            "Раздел управления напоминаниями пока в разработке."
            " Следите за обновлениями."
        )


__all__ = ["router"]
