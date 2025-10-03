"""Маршрутизатор пользовательского каталога олимпиад."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.catalog import (
    BACK_TO_SUBJECTS_CALLBACK,
    build_olympiads_keyboard,
    build_subjects_keyboard,
)
from bot.services.olympiad_service import get_olympiad_service
from bot.utils import texts


router = Router(name="user_catalog")


def _format_catalog_intro() -> str:
    lines = [texts.MAIN_MENU_CATALOG, ""]
    lines.extend(texts.CATALOG_HINT)
    return "\n".join(lines)


def _format_olympiads_text(subject_title: str, olympiads: list) -> str:
    lines: list[str] = [f"📚 {subject_title}", ""]
    if olympiads:
        lines.append("Доступные олимпиады:")
        for item in olympiads:
            details: list[str] = []
            if item.reg_deadline:
                details.append(f"регистрация до {item.reg_deadline.strftime('%d.%m.%Y')}")
            if item.round_date:
                details.append(f"тур {item.round_date.strftime('%d.%m.%Y')}")
            suffix = f" ({', '.join(details)})" if details else ""
            lines.append(f"• {item.title}{suffix}")
            if item.description:
                lines.append(f"  {item.description}")
        lines.append("")
        lines.append("Нажмите кнопку ниже, чтобы добавить олимпиаду в ❤ Мои олимпиады.")
    else:
        lines.append("Список олимпиад для этого предмета появится позже.")
    return "\n".join(lines)


async def _show_subjects(message: Message, *, edit: bool = False) -> None:
    service = get_olympiad_service()
    subjects = [(subject.code, subject.title) for subject in service.list_subjects()]
    keyboard = build_subjects_keyboard(subjects)
    text = _format_catalog_intro()
    if edit:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)


@router.message(Command("catalog"))
async def handle_catalog_command(message: Message) -> None:
    """Открыть каталог по команде."""

    await _show_subjects(message, edit=False)


@router.callback_query(F.data == "menu:catalog")
async def open_catalog_from_menu(callback: CallbackQuery) -> None:
    """Показать список предметов из главного меню."""

    await callback.answer()
    message = callback.message
    if message is None:
        return
    await _show_subjects(message, edit=False)


@router.callback_query(F.data.startswith("subj:"))
async def handle_subject_selection(callback: CallbackQuery) -> None:
    """Показать список олимпиад выбранного предмета."""

    await callback.answer()

    message = callback.message
    if message is None:
        return

    payload = callback.data or ""
    if payload == BACK_TO_SUBJECTS_CALLBACK:
        await _show_subjects(message, edit=True)
        return

    _, _, subject_code = payload.partition(":")

    service = get_olympiad_service()
    subject = service.get_subject(subject_code)
    if subject is None:
        await message.answer("Не удалось найти такой предмет в каталоге.")
        return

    olympiads = list(service.list_olympiads(subject.code))
    keyboard = build_olympiads_keyboard([(item.id, item.title) for item in olympiads])
    text = _format_olympiads_text(subject.title, olympiads)
    await message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("olymp:"))
async def handle_add_to_favorites(callback: CallbackQuery) -> None:
    """Добавить выбранную олимпиаду в избранное пользователя."""

    payload = callback.data or ""
    _, _, raw_id = payload.partition(":")
    try:
        olympiad_id = int(raw_id)
    except ValueError:
        await callback.answer("Не удалось определить олимпиаду", show_alert=True)
        return

    message = callback.message
    if message is None:
        await callback.answer("Команда доступна только в чате", show_alert=True)
        return

    service = get_olympiad_service()
    try:
        added = await service.add_to_favorites(
            tg_user_id=callback.from_user.id,
            olympiad_id=olympiad_id,
            username=callback.from_user.username,
        )
    except ValueError:
        await callback.answer("Олимпиада недоступна", show_alert=True)
        return

    if added:
        confirmation = "\n".join(texts.CONFIRM_FAVORITE_ADDED)
        await message.answer(confirmation)
        await callback.answer("Добавлено в избранное ✨")
    else:
        await callback.answer("Эта олимпиада уже в избранном", show_alert=True)


__all__ = ["router"]
