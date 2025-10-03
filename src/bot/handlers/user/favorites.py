"""Маршрутизатор избранных олимпиад."""

from __future__ import annotations

from typing import Sequence

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from ...keyboards.favorites import (
    REMOVE_CALLBACK_PREFIX,
    build_favorites_keyboard,
)
from ...services.favorites_service import FavoriteOlympiad, get_favorites_service
from ...utils import texts

router = Router(name="user_favorites")


async def _format_favorites_text(tg_user_id: int) -> tuple[str, Sequence[FavoriteOlympiad]]:
    """Получить текст и данные об избранных олимпиадах."""

    service = get_favorites_service()
    favorites = await service.list_favorites(tg_user_id=tg_user_id)

    lines: list[str] = [texts.MAIN_MENU_FAVORITES, ""]
    if favorites:
        lines.append("Ваши отмеченные олимпиады:")
        for item in favorites:
            meta: list[str] = []
            if item.reg_deadline:
                meta.append(f"регистрация до {item.reg_deadline.strftime('%d.%m.%Y')}")
            if item.round_date:
                meta.append(f"тур {item.round_date.strftime('%d.%m.%Y')}")
            suffix = f" ({', '.join(meta)})" if meta else ""
            lines.append(f"• {item.title}{suffix}")
            if item.description:
                lines.append(f"  {item.description}")
        lines.extend(
            [
                "",
                "Нажмите «📚 Материалы для подготовки», чтобы получить подборку ссылок.",
                "Кнопка «🗑 Удалить» убирает олимпиаду из списка.",
            ]
        )
    else:
        lines.append(
            "Пока список пуст. Добавьте олимпиады через каталог — мы напомним о важных датах."
        )

    return "\n".join(lines), favorites


async def _send_favorites(message: Message, user_id: int, *, edit: bool = False) -> None:
    text, favorites = await _format_favorites_text(user_id)
    keyboard = build_favorites_keyboard(favorites)

    if edit:
        try:
            await message.edit_text(text, reply_markup=keyboard)
            return
        except TelegramBadRequest:
            pass
    await message.answer(text, reply_markup=keyboard)


@router.message(Command("favorites"))
async def handle_favorites_command(message: Message) -> None:
    """Показать список избранных олимпиад."""

    user = message.from_user
    if user is None:
        return
    await _send_favorites(message, user.id, edit=False)


@router.callback_query(F.data == "menu:favorites")
async def open_favorites_from_menu(callback: CallbackQuery) -> None:
    """Открыть избранные олимпиады из главного меню."""

    await callback.answer()
    message = callback.message
    if message is None:
        return
    await _send_favorites(message, callback.from_user.id, edit=False)


@router.callback_query(F.data.startswith(REMOVE_CALLBACK_PREFIX))
async def handle_remove_favorite(callback: CallbackQuery) -> None:
    """Удалить олимпиаду из избранного."""

    payload = callback.data or ""
    raw_id = payload.removeprefix(REMOVE_CALLBACK_PREFIX)
    try:
        olympiad_id = int(raw_id)
    except ValueError:
        await callback.answer("Не удалось определить олимпиаду", show_alert=True)
        return

    service = get_favorites_service()
    removed = await service.remove_favorite(
        tg_user_id=callback.from_user.id,
        olympiad_id=olympiad_id,
    )
    if removed:
        await callback.answer("Олимпиада удалена")
    else:
        await callback.answer("Этой олимпиады нет в списке", show_alert=True)

    message = callback.message
    if message is not None:
        await _send_favorites(message, callback.from_user.id, edit=True)


__all__ = ["router"]
