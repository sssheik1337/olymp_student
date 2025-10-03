"""Маршрутизатор информации о ВУЗах и поступлении."""

from __future__ import annotations

from typing import Sequence

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.universities import (
    BACK_TO_LIST_CALLBACK,
    UNIVERSITY_CALLBACK_PREFIX,
    build_universities_keyboard,
    build_university_details_keyboard,
)
from bot.services.universities_service import (
    UniversityDetail,
    UniversityRecommendation,
    get_universities_service,
)
from bot.utils import texts

router = Router(name="user_universities")


def _format_universities_overview(
    recommendations: Sequence[UniversityRecommendation],
) -> str:
    """Сформировать текст списка рекомендованных ВУЗов."""

    lines: list[str] = [texts.MAIN_MENU_UNIVERSITIES, ""]
    lines.extend(texts.UNIVERSITIES_HINT)
    lines.append("")

    if not recommendations:
        lines.append(
            "Пока что мы не нашли подходящих ВУЗов. Добавьте олимпиады через каталог — "
            "и мы подберём льготы автоматически."
        )
        return "\n".join(lines).strip()

    lines.append("Подобрали университеты, где учитывают ваши олимпиады:")
    for item in recommendations:
        lines.append(f"• {item.name}")
        lines.append(f"  {item.description}")
        if item.matched_olympiads:
            lines.append(
                "  Подходит за: " + ", ".join(sorted(item.matched_olympiads)) + "."
            )
        if item.benefits:
            lines.append("  Льготы:")
            for benefit in item.benefits:
                lines.append(f"    • {benefit}")
        lines.append("")

    return "\n".join(lines).strip()


def _format_university_details(detail: UniversityDetail) -> str:
    """Подготовить текст детализации по одному ВУЗу."""

    lines: list[str] = [f"🎓 {detail.name}", ""]
    lines.append(detail.description)
    lines.append("")
    if detail.matched_olympiads:
        lines.append("Ваши достижения учитываются в приёме:")
        for title in sorted(detail.matched_olympiads):
            lines.append(f"• {title}")
        lines.append("")
    if detail.benefits:
        lines.append("Какие льготы доступны:")
        for benefit in detail.benefits:
            lines.append(f"• {benefit}")
        lines.append("")
    if detail.faculties:
        lines.append("Факультеты и направления:")
        for faculty in detail.faculties:
            lines.append(f"🏫 {faculty.title}")
            lines.append(f"   {faculty.description}")
            if faculty.benefits:
                for benefit in faculty.benefits:
                    lines.append(f"   • {benefit}")
            lines.append("")
    return "\n".join(lines).strip()


async def _send_universities_overview(
    message: Message,
    tg_user_id: int,
    *,
    edit: bool,
) -> None:
    """Показать список рекомендованных ВУЗов."""

    service = get_universities_service()
    recommendations = await service.list_recommendations(tg_user_id=tg_user_id)
    text = _format_universities_overview(recommendations)
    keyboard = build_universities_keyboard(
        [(item.id, item.name) for item in recommendations]
    )

    if edit:
        try:
            await message.edit_text(text, reply_markup=keyboard)
            return
        except TelegramBadRequest:
            pass
    await message.answer(text, reply_markup=keyboard)


@router.message(Command("universities"))
async def open_universities_command(message: Message) -> None:
    """Показать раздел ВУЗов по команде."""

    user = message.from_user
    if user is None:
        return
    await _send_universities_overview(message, user.id, edit=False)


@router.callback_query(F.data == "menu:universities")
async def open_universities_from_menu(callback: CallbackQuery) -> None:
    """Открыть раздел ВУЗов из главного меню."""

    await callback.answer()
    message = callback.message
    if message is None:
        return
    await _send_universities_overview(message, callback.from_user.id, edit=False)


@router.callback_query(F.data == BACK_TO_LIST_CALLBACK)
async def return_to_universities_list(callback: CallbackQuery) -> None:
    """Вернуться к списку рекомендаций."""

    await callback.answer()
    message = callback.message
    if message is None:
        return
    await _send_universities_overview(message, callback.from_user.id, edit=True)


@router.callback_query(F.data.startswith(UNIVERSITY_CALLBACK_PREFIX))
async def open_university_details(callback: CallbackQuery) -> None:
    """Показать детализацию по конкретному ВУЗу."""

    await callback.answer()
    message = callback.message
    if message is None:
        return

    payload = callback.data or ""
    raw_id = payload.removeprefix(UNIVERSITY_CALLBACK_PREFIX)
    try:
        university_id = int(raw_id)
    except ValueError:
        await message.answer("Не удалось определить университет. Попробуйте ещё раз.")
        return

    service = get_universities_service()
    detail = await service.get_details(
        tg_user_id=callback.from_user.id, university_id=university_id
    )
    if detail is None:
        await message.answer(
            "Информация недоступна. Убедитесь, что подходящие олимпиады добавлены в избранное.",
        )
        return

    text = _format_university_details(detail)
    keyboard = build_university_details_keyboard()
    try:
        await message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        await message.answer(text, reply_markup=keyboard)


__all__ = ["router"]
