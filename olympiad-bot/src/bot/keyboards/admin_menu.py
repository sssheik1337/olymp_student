"""Инлайн-клавиатура административного раздела."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

ADMIN_MATERIALS_CALLBACK = "admin:materials"
ADMIN_OLYMPIADS_CALLBACK = "admin:olympiads"
ADMIN_REMINDERS_CALLBACK = "admin:reminders"
ADMIN_BACK_CALLBACK = "admin:menu"


_DEF_BUTTONS: tuple[tuple[str, str], ...] = (
    ("📚 Материалы", ADMIN_MATERIALS_CALLBACK),
    ("🏆 Олимпиады", ADMIN_OLYMPIADS_CALLBACK),
    ("⏰ Напоминания", ADMIN_REMINDERS_CALLBACK),
)


def build_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Собрать клавиатуру для панели администратора."""

    inline_keyboard: list[list[InlineKeyboardButton]] = []
    for text, callback_data in _DEF_BUTTONS:
        inline_keyboard.append(
            [InlineKeyboardButton(text=text, callback_data=callback_data)]
        )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


__all__ = [
    "ADMIN_BACK_CALLBACK",
    "ADMIN_MATERIALS_CALLBACK",
    "ADMIN_OLYMPIADS_CALLBACK",
    "ADMIN_REMINDERS_CALLBACK",
    "build_admin_menu_keyboard",
]
