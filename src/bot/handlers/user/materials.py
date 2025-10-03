"""Маршрутизатор материалов для подготовки."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from ...keyboards.favorites import MATERIALS_CALLBACK_PREFIX
from ...services.materials_service import get_materials_service
from ...services.olympiad_service import get_olympiad_service

router = Router(name="user_materials")


def _format_materials_text(olympiad_title: str, bundle) -> str:
    """Сформировать текст с подборкой материалов."""

    lines = ["📚 Материалы для подготовки", ""]
    lines.append(f"Для олимпиады: {olympiad_title}")
    lines.append("")

    categories = [
        ("Задачи прошлых лет", bundle.past_problems),
        ("Теория и видеоразборы", bundle.theory),
        ("Полезные статьи и методички", bundle.articles),
    ]
    for title, links in categories:
        lines.append(f"{title}:")
        if links:
            for link in links:
                lines.append(f"• {link.title} — {link.url}")
        else:
            lines.append("• материалы появятся позже")
        lines.append("")

    if bundle.additional:
        lines.append("Дополнительные материалы от администраторов:")
        for link in bundle.additional:
            lines.append(f"• {link.title} — {link.url}")
        lines.append("")

    lines.append(
        "Не нашли нужное? Нажмите «📚 Материалы для подготовки» в разделе ❤ Мои олимпиады,"
    )
    lines.append("и мы добавим новые материалы вручную.")
    return "\n".join(lines).strip()


@router.message(F.text == "📚 Материалы для подготовки")
async def handle_materials_request(message: Message) -> None:
    """Текстовый запрос на материалы (заглушка)."""

    await message.answer(
        "Мы получили запрос на подбор материалов. Свяжемся с вами после обновления базы."
    )


@router.callback_query(F.data.startswith(MATERIALS_CALLBACK_PREFIX))
async def show_favorite_materials(callback: CallbackQuery) -> None:
    """Показать материалы для выбранной олимпиады из избранного."""

    payload = callback.data or ""
    raw_id = payload.removeprefix(MATERIALS_CALLBACK_PREFIX)
    try:
        olympiad_id = int(raw_id)
    except ValueError:
        await callback.answer("Не удалось найти материалы", show_alert=True)
        return

    materials_service = get_materials_service()
    bundle = await materials_service.get_materials(olympiad_id)

    olympiad_service = get_olympiad_service()
    olympiad = olympiad_service.get_olympiad(olympiad_id)
    title = olympiad.title if olympiad else "выбранная олимпиада"

    message = callback.message
    if message is not None:
        text = _format_materials_text(title, bundle)
        await message.answer(text, disable_web_page_preview=True)
    await callback.answer("Материалы отправлены")


__all__ = ["router"]
