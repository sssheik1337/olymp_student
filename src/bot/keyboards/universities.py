"""Инлайн-клавиатуры раздела ВУЗов."""

from __future__ import annotations

from typing import Sequence

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..utils import texts

UNIVERSITY_CALLBACK_PREFIX = "uni:"
BACK_TO_LIST_CALLBACK = "universities:list"


def build_universities_keyboard(
    recommendations: Sequence[tuple[int, str]],
) -> InlineKeyboardMarkup:
    """Клавиатура списка рекомендованных ВУЗов."""

    builder = InlineKeyboardBuilder()
    for uni_id, uni_name in recommendations:
        builder.button(
            text=uni_name,
            callback_data=f"{UNIVERSITY_CALLBACK_PREFIX}{uni_id}",
        )
    builder.button(text=texts.MAIN_MENU_FAVORITES, callback_data="menu:favorites")
    builder.button(text=texts.MAIN_MENU_CATALOG, callback_data="menu:catalog")
    builder.adjust(1)
    return builder.as_markup()


def build_university_details_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура экранов с деталями по конкретному ВУЗу."""

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ К списку ВУЗов", callback_data=BACK_TO_LIST_CALLBACK)
    builder.button(text=texts.MAIN_MENU_FAVORITES, callback_data="menu:favorites")
    builder.button(text=texts.MAIN_MENU_CATALOG, callback_data="menu:catalog")
    builder.adjust(1)
    return builder.as_markup()


__all__ = [
    "BACK_TO_LIST_CALLBACK",
    "UNIVERSITY_CALLBACK_PREFIX",
    "build_universities_keyboard",
    "build_university_details_keyboard",
]
