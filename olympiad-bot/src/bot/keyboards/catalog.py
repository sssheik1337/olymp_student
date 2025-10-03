"""Инлайн-клавиатуры для навигации по каталогу олимпиад."""

from __future__ import annotations

from collections.abc import Sequence

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


BACK_TO_SUBJECTS_CALLBACK = "subj:__back__"


def build_subjects_keyboard(subjects: Sequence[tuple[str, str]]) -> InlineKeyboardMarkup:
    """Построить клавиатуру со списком учебных предметов."""

    builder = InlineKeyboardBuilder()
    for code, title in subjects:
        builder.button(text=title, callback_data=f"subj:{code}")
    if not subjects:
        builder.button(text="Каталог временно пуст", callback_data=BACK_TO_SUBJECTS_CALLBACK)
    builder.adjust(1)
    return builder.as_markup()


def build_olympiads_keyboard(
    olympiads: Sequence[tuple[int, str]], *, include_back: bool = True
) -> InlineKeyboardMarkup:
    """Построить клавиатуру со списком олимпиад выбранного предмета."""

    builder = InlineKeyboardBuilder()
    for olympiad_id, title in olympiads:
        builder.button(text=f"⭐ {title}", callback_data=f"olymp:{olympiad_id}")
    if include_back:
        builder.button(text="← Назад к предметам", callback_data=BACK_TO_SUBJECTS_CALLBACK)
    builder.adjust(1)
    return builder.as_markup()


__all__ = [
    "BACK_TO_SUBJECTS_CALLBACK",
    "build_subjects_keyboard",
    "build_olympiads_keyboard",
]
