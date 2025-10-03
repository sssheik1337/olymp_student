"""Обработчик команды /start."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.main_menu import build_main_menu_keyboard
from bot.utils import texts

router = Router(name="common_start")

@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    """Отправить приветственное сообщение с главным меню."""

    keyboard = build_main_menu_keyboard()
    await message.answer("\n".join(texts.START_GREETING_LINES), reply_markup=keyboard)
