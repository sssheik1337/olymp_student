"""Маршрутизатор заглушки синхронизации календаря."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from ...keyboards.calendar import build_calendar_keyboard
from ...services.calendar_service_stub import get_calendar_service
from ...utils import texts

router = Router(name="user_calendar_sync_stub")


def _format_calendar_text(link: str) -> str:
    lines: list[str] = [texts.MAIN_MENU_CALENDAR, ""]
    lines.extend(texts.CALENDAR_HINT)
    lines.append("")
    lines.append(f"🔗 Уникальная ссылка: {link}")
    lines.append("")
    lines.append("После подключения вернитесь и подтвердите синхронизацию.")
    return "\n".join(lines)


async def _send_calendar_screen(message: Message, link: str, *, edit: bool) -> None:
    text = _format_calendar_text(link)
    keyboard = build_calendar_keyboard()
    if edit:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)


@router.message(Command("calendar"))
async def open_calendar_command(message: Message) -> None:
    """Показать раздел синхронизации по команде."""

    service = get_calendar_service()
    user_id = message.from_user.id if message.from_user else 0
    link = service.generate_unique_link(user_id)
    await _send_calendar_screen(message, link, edit=False)


@router.callback_query(F.data == "menu:calendar")
async def open_calendar_from_menu(callback: CallbackQuery) -> None:
    """Открыть раздел из главного меню."""

    await callback.answer()
    message = callback.message
    if message is None:
        return
    service = get_calendar_service()
    link = service.generate_unique_link(callback.from_user.id)
    await _send_calendar_screen(message, link, edit=True)


@router.callback_query(F.data == "calendar:link")
async def refresh_calendar_link(callback: CallbackQuery) -> None:
    """Сгенерировать новую уникальную ссылку."""

    service = get_calendar_service()
    link = service.generate_unique_link(callback.from_user.id)
    message = callback.message
    if message is not None:
        await _send_calendar_screen(message, link, edit=True)
    await callback.answer("Ссылка обновлена")


@router.callback_query(F.data == "calendar:confirm")
async def confirm_calendar_sync(callback: CallbackQuery) -> None:
    """Подтвердить синхронизацию (заглушка)."""

    service = get_calendar_service()
    service.confirm_synchronization(callback.from_user.id)
    await callback.answer("Готово!", show_alert=False)
    message = callback.message
    if message is not None:
        confirmation = "\n".join(texts.CONFIRM_CALENDAR_SYNC)
        await message.answer(confirmation)


__all__ = ["router"]
