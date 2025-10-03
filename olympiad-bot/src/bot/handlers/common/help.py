"""Обработчик команды /help."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ...utils import texts

router = Router(name="common_help")

@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """Отправить краткую инструкцию по разделам бота."""

    await message.answer("\n".join(texts.HELP_TEXT_LINES))
