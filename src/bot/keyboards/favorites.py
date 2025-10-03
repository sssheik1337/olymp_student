"""Инлайн-клавиатура раздела избранных олимпиад."""

from __future__ import annotations

from typing import Sequence

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..services.favorites_service import FavoriteOlympiad
from ..utils import texts

MATERIALS_CALLBACK_PREFIX = "fav:materials:"
REMOVE_CALLBACK_PREFIX = "fav:remove:"


def build_favorites_keyboard(favorites: Sequence[FavoriteOlympiad]) -> InlineKeyboardMarkup:
    """Создать клавиатуру управления избранными олимпиадами."""

    builder = InlineKeyboardBuilder()
    for item in favorites:
        builder.button(
            text="📚 Материалы для подготовки",
            callback_data=f"{MATERIALS_CALLBACK_PREFIX}{item.olympiad_id}",
        )
        builder.button(
            text="🗑 Удалить",
            callback_data=f"{REMOVE_CALLBACK_PREFIX}{item.olympiad_id}",
        )

    builder.button(text=texts.MAIN_MENU_CATALOG, callback_data="menu:catalog")

    row_sizes = [2] * len(favorites) + [1]
    builder.adjust(*row_sizes if row_sizes else (1,))
    return builder.as_markup()


__all__ = [
    "MATERIALS_CALLBACK_PREFIX",
    "REMOVE_CALLBACK_PREFIX",
    "build_favorites_keyboard",
]
