"""Инлайн-клавиатуры раздела подписки."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..utils import texts

PAY_CALLBACK = "subscription:pay"
CONFIRM_CALLBACK = "subscription:confirm"
BACK_TO_SUBSCRIPTION_CALLBACK = "menu:subscription"


def build_subscription_overview_keyboard(*, is_subscribed: bool) -> InlineKeyboardMarkup:
    """Клавиатура со ссылкой на оформление подписки."""

    builder = InlineKeyboardBuilder()
    action_text = "Оформить подписку" if not is_subscribed else "Продлить подписку"
    builder.button(text=f"💳 {action_text}", callback_data=PAY_CALLBACK)
    builder.button(text=texts.MAIN_MENU_HELP, callback_data="menu:help")
    builder.adjust(1)
    return builder.as_markup()


def build_subscription_payment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения оплаты подписки."""

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Оплачено", callback_data=CONFIRM_CALLBACK)
    builder.button(text="⬅️ Вернуться", callback_data=BACK_TO_SUBSCRIPTION_CALLBACK)
    builder.adjust(1)
    return builder.as_markup()


__all__ = [
    "BACK_TO_SUBSCRIPTION_CALLBACK",
    "CONFIRM_CALLBACK",
    "PAY_CALLBACK",
    "build_subscription_overview_keyboard",
    "build_subscription_payment_keyboard",
]
