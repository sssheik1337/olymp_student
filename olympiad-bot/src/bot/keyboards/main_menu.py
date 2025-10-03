"""Инлайн-клавиатура главного меню."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..utils import texts


MENU_CALLBACKS: tuple[tuple[str, str], ...] = (
    (texts.MAIN_MENU_FAVORITES, "menu:favorites"),
    (texts.MAIN_MENU_CATALOG, "menu:catalog"),
    (texts.MAIN_MENU_CALENDAR, "menu:calendar"),
    (texts.MAIN_MENU_UNIVERSITIES, "menu:universities"),
    (texts.MAIN_MENU_SUBSCRIPTION, "menu:subscription"),
    (texts.MAIN_MENU_HELP, "menu:help"),
)


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Собрать инлайн-клавиатуру из шести пунктов меню."""

    builder = InlineKeyboardBuilder()
    for text, callback_data in MENU_CALLBACKS:
        builder.button(text=text, callback_data=callback_data)
    builder.adjust(2, 2, 2)
    return builder.as_markup()


__all__ = ["build_main_menu_keyboard"]
