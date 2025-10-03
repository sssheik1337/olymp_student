"""Точка входа бота олимпиад."""

from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from bot.config import get_config
from bot.handlers.admin import materials as admin_materials_router
from bot.handlers.admin import panel as admin_panel_router
from bot.handlers.common import help as help_router
from bot.handlers.common import start as start_router
from bot.handlers.user import calendar_sync_stub as calendar_sync_router
from bot.handlers.user import catalog as catalog_router
from bot.handlers.user import favorites as favorites_router
from bot.handlers.user import materials as materials_router
from bot.handlers.user import subscription_stub as subscription_router
from bot.handlers.user import universities as universities_router
from bot.middlewares.subscription_gate import SubscriptionGateMiddleware
from bot.utils.logging import logger, setup_logging
from bot.utils.scheduler import shutdown_scheduler, start_scheduler


async def _set_default_commands(bot: Bot) -> None:
    """Задать команды /start и /help в интерфейсе Telegram."""

    commands = [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="help", description="Справка по разделам"),
    ]
    await bot.set_my_commands(commands)


async def main() -> None:
    """Запустить бота в режиме long polling."""

    setup_logging()
    config = get_config()
    logger.info("Запуск бота олимпиад")

    bot = Bot(token=config.bot_token, parse_mode="HTML")
    dp = Dispatcher()

    subscription_gate = SubscriptionGateMiddleware()
    dp.message.middleware(subscription_gate)
    dp.callback_query.middleware(subscription_gate)

    dp.include_router(start_router.router)
    dp.include_router(help_router.router)
    dp.include_router(catalog_router.router)
    dp.include_router(favorites_router.router)
    dp.include_router(materials_router.router)
    dp.include_router(subscription_router.router)
    dp.include_router(calendar_sync_router.router)
    dp.include_router(universities_router.router)
    dp.include_router(admin_panel_router.router)
    dp.include_router(admin_materials_router.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await _set_default_commands(bot)

    start_scheduler()

    try:
        await dp.start_polling(bot)
    finally:
        shutdown_scheduler()
        logger.info("Остановка бота олимпиад")


if __name__ == "__main__":
    asyncio.run(main())
