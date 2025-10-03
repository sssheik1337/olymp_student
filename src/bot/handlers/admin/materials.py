"""Маршрутизатор управления материалами в админке."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from typing import Sequence

from bot.config import get_config
from bot.keyboards.admin_menu import ADMIN_BACK_CALLBACK, ADMIN_MATERIALS_CALLBACK
from bot.services.materials_service import (
    AdminMaterial,
    MaterialsService,
    get_materials_service,
)

router = Router(name="admin_materials")

_settings = get_config()
_admin_ids = set(_settings.admin_ids)
_service: MaterialsService = get_materials_service()

ADD_MATERIAL_CALLBACK = "admin:materials:add"
EDIT_MATERIAL_PREFIX = "admin:materials:edit:"
DELETE_MATERIAL_PREFIX = "admin:materials:delete:"
LIST_MATERIALS_CALLBACK = ADMIN_MATERIALS_CALLBACK


class MaterialForm(StatesGroup):
    """Состояния ввода данных о материале."""

    waiting_for_olympiad_id = State()
    waiting_for_title = State()
    waiting_for_url = State()


def _is_admin(user_id: int | None) -> bool:
    return user_id is not None and user_id in _admin_ids


def _format_materials_overview(materials: Sequence[AdminMaterial]) -> str:
    if not materials:
        return (
            "Материалы ещё не добавлены."
            "\nИспользуйте кнопку «➕ Добавить материал», чтобы загрузить первый ресурс."
        )

    lines = ["Материалы для подготовки:", ""]
    for item in materials:
        lines.append(
            f"#{item.id}: {item.title} (олимпиада {item.olympiad_id})"
        )
        lines.append(f"↗ {item.url}")
        if item.added_by_admin_id:
            lines.append(f"Добавил администратор: {item.added_by_admin_id}")
        lines.append("")
    lines.append("Выберите действие ниже, чтобы обновить или удалить запись.")
    return "\n".join(lines)


def _build_materials_keyboard(materials: Sequence[AdminMaterial]):
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    inline_keyboard: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="➕ Добавить материал", callback_data=ADD_MATERIAL_CALLBACK)]
    ]
    for item in materials:
        inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"✏️ Редактировать #{item.id}",
                    callback_data=f"{EDIT_MATERIAL_PREFIX}{item.id}",
                ),
                InlineKeyboardButton(
                    text=f"🗑 Удалить #{item.id}",
                    callback_data=f"{DELETE_MATERIAL_PREFIX}{item.id}",
                ),
            ]
        )
    inline_keyboard.append(
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=ADMIN_BACK_CALLBACK)]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def _send_materials_overview(message: Message, *, edit: bool = False) -> None:
    materials = await _service.list_admin_materials()
    text = _format_materials_overview(materials)
    keyboard = _build_materials_keyboard(materials)
    if edit:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)


async def _reject_non_admin(callback: CallbackQuery) -> bool:
    user = callback.from_user
    if not _is_admin(user.id if user else None):
        await callback.answer("Недостаточно прав", show_alert=True)
        return True
    return False


async def _reject_non_admin_message(message: Message, state: FSMContext) -> bool:
    user = message.from_user
    if not _is_admin(user.id if user else None):
        await message.answer("Эта функция доступна только администраторам.")
        await state.clear()
        return True
    return False


@router.callback_query(F.data == LIST_MATERIALS_CALLBACK)
async def list_materials(callback: CallbackQuery) -> None:
    """Показать список материалов в админ-панели."""

    if await _reject_non_admin(callback):
        return

    message = callback.message
    if message is None:
        await callback.answer()
        return

    await callback.answer()
    await _send_materials_overview(message, edit=True)


@router.message(Command("admin_materials"))
async def list_materials_command(message: Message) -> None:
    """Сервисная команда для быстрого доступа к управлению материалами."""

    if not _is_admin(message.from_user.id if message.from_user else None):
        await message.answer("Команда доступна только администраторам.")
        return

    await _send_materials_overview(message, edit=False)


@router.callback_query(F.data == ADD_MATERIAL_CALLBACK)
async def start_add_material(callback: CallbackQuery, state: FSMContext) -> None:
    """Запросить данные для создания нового материала."""

    if await _reject_non_admin(callback):
        return

    await callback.answer()
    message = callback.message
    if message is not None:
        try:
            await message.edit_reply_markup()
        except TelegramBadRequest:
            pass

    await state.set_state(MaterialForm.waiting_for_olympiad_id)
    await state.update_data(mode="create")

    if message is not None:
        await message.answer(
            "Введите ID олимпиады, к которой относится материал."
        )


@router.callback_query(F.data.startswith(EDIT_MATERIAL_PREFIX))
async def start_edit_material(callback: CallbackQuery, state: FSMContext) -> None:
    """Начать процесс обновления материала."""

    if await _reject_non_admin(callback):
        return

    payload = callback.data or ""
    raw_id = payload.removeprefix(EDIT_MATERIAL_PREFIX)
    try:
        material_id = int(raw_id)
    except ValueError:
        await callback.answer("Некорректный идентификатор", show_alert=True)
        return

    material = await _service.get_material(material_id)
    if material is None:
        await callback.answer("Материал не найден", show_alert=True)
        return

    await callback.answer()
    message = callback.message
    if message is not None:
        try:
            await message.edit_reply_markup()
        except TelegramBadRequest:
            pass

    await state.set_state(MaterialForm.waiting_for_olympiad_id)
    await state.update_data(
        mode="edit",
        material_id=material.id,
        prev_title=material.title,
        prev_url=material.url,
    )

    prompt = (
        "Редактирование материала #{id}."
        "\nТекущий ID олимпиады: {olympiad}."
        "\nНазвание: {title}."
        "\nСсылка: {url}."
        "\nВведите новый ID олимпиады.".format(
            id=material.id,
            olympiad=material.olympiad_id,
            title=material.title,
            url=material.url,
        )
    )
    if message is not None:
        await message.answer(prompt)


@router.callback_query(F.data.startswith(DELETE_MATERIAL_PREFIX))
async def delete_material(callback: CallbackQuery) -> None:
    """Удалить материал из базы."""

    if await _reject_non_admin(callback):
        return

    payload = callback.data or ""
    raw_id = payload.removeprefix(DELETE_MATERIAL_PREFIX)
    try:
        material_id = int(raw_id)
    except ValueError:
        await callback.answer("Некорректный идентификатор", show_alert=True)
        return

    success = await _service.delete_material(material_id)
    if not success:
        await callback.answer("Материал уже удалён", show_alert=True)
        return

    await callback.answer("Материал удалён")
    message = callback.message
    if message is not None:
        await _send_materials_overview(message, edit=True)


@router.message(MaterialForm.waiting_for_olympiad_id)
async def process_olympiad_id(message: Message, state: FSMContext) -> None:
    """Сохранить olympiad_id и запросить название."""

    if await _reject_non_admin_message(message, state):
        return

    try:
        olympiad_id = int((message.text or "").strip())
    except ValueError:
        await message.answer("Введите числовой ID олимпиады.")
        return

    await state.update_data(olympiad_id=olympiad_id)
    await state.set_state(MaterialForm.waiting_for_title)
    data = await state.get_data()
    if data.get("mode") == "edit":
        prev_title = data.get("prev_title")
        hint = f"Введите новое название (сейчас: {prev_title})."
    else:
        hint = "Введите название материала."
    await message.answer(hint)


@router.message(MaterialForm.waiting_for_title)
async def process_title(message: Message, state: FSMContext) -> None:
    """Сохранить название и запросить ссылку."""

    if await _reject_non_admin_message(message, state):
        return

    title = (message.text or "").strip()
    if not title:
        await message.answer("Название не может быть пустым. Попробуйте снова.")
        return

    await state.update_data(title=title)
    await state.set_state(MaterialForm.waiting_for_url)
    data = await state.get_data()
    if data.get("mode") == "edit":
        prev_url = data.get("prev_url")
        hint = f"Отправьте новую ссылку (сейчас: {prev_url})."
    else:
        hint = "Отправьте ссылку на материал."
    await message.answer(hint)


@router.message(MaterialForm.waiting_for_url)
async def process_url(message: Message, state: FSMContext) -> None:
    """Завершить создание или обновление материала."""

    if await _reject_non_admin_message(message, state):
        return

    url = (message.text or "").strip()
    if not url:
        await message.answer("Ссылка не может быть пустой. Попробуйте снова.")
        return

    data = await state.get_data()
    olympiad_id = data.get("olympiad_id")
    title = data.get("title")
    mode = data.get("mode")

    await state.clear()

    if olympiad_id is None or title is None:
        await message.answer("Не удалось обработать данные. Начните заново.")
        return

    admin_id = message.from_user.id if message.from_user else None
    if admin_id is None:
        await message.answer("Не удалось определить администратора.")
        return

    if mode == "edit":
        material_id = data.get("material_id")
        if material_id is None:
            await message.answer("Не удалось определить материал для обновления.")
            return
        updated = await _service.update_material(
            material_id=material_id,
            olympiad_id=olympiad_id,
            title=title,
            url=url,
            admin_tg_id=admin_id,
        )
        if not updated:
            await message.answer("Материал не найден или был удалён.")
            return
        await message.answer("Материал обновлён.")
    else:
        await _service.create_material(
            olympiad_id=olympiad_id,
            title=title,
            url=url,
            admin_tg_id=admin_id,
        )
        await message.answer("Материал добавлен.")

    await _send_materials_overview(message, edit=False)


__all__ = ["router"]
