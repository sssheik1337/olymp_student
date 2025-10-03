"""Инлайн-клавиатура раздела синхронизации с календарем."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..utils import texts


CALENDAR_BUTTONS: tuple[tuple[str, str], ...] = (
    ("🔗 Получить ссылку", "calendar:link"),
    ("✅ Подтвердить синхронизацию", "calendar:confirm"),
    (texts.MAIN_MENU_FAVORITES, "menu:favorites"),
)


def build_calendar_keyboard() -> InlineKeyboardMarkup:
    """Собрать клавиатуру для раздела календаря."""

    builder = InlineKeyboardBuilder()
    for text, callback_data in CALENDAR_BUTTONS:
        builder.button(text=text, callback_data=callback_data)
    builder.adjust(1)
    return builder.as_markup()


__all__ = ["build_calendar_keyboard"]
