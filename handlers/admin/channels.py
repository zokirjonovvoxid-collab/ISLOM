"""Admin flows for managing mandatory and optional subscription channels."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from fluentogram import TranslatorRunner

from db import Database
from services.subscription import normalize_channel_reference
from states.states import AddChannel, RemoveChannel

router = Router(name="admin_channels")

ADD_MANDATORY_TEXTS = {"➕ Majburiy kanal qo'shish", "➕ Добавить обязательный канал", "➕ Add mandatory channel"}
REMOVE_MANDATORY_TEXTS = {"➖ Majburiy kanal o'chirish", "➖ Удалить обязательный канал", "➖ Remove mandatory channel"}
ADD_OPTIONAL_TEXTS = {
    "➕ Majburiy bo'lmagan kanal qo'shish", "➕ Добавить необязательный канал", "➕ Add optional channel"
}
REMOVE_OPTIONAL_TEXTS = {
    "➖ Majburiy bo'lmagan kanal o'chirish", "➖ Удалить необязательный канал", "➖ Remove optional channel"
}


# Use the normalization from subscription.py for consistency
# No need for local version - import it instead


@router.message(F.text.in_(ADD_MANDATORY_TEXTS))
async def start_add_mandatory(message: Message, i18n: TranslatorRunner, state: FSMContext) -> None:
    await state.update_data(mandatory=True)
    await state.set_state(AddChannel.waiting_chat_id)
    await message.answer(i18n.get("admin-ask-channel-id"))


@router.message(F.text.in_(ADD_OPTIONAL_TEXTS))
async def start_add_optional(message: Message, i18n: TranslatorRunner, state: FSMContext) -> None:
    await state.update_data(mandatory=False)
    await state.set_state(AddChannel.waiting_chat_id)
    await message.answer(i18n.get("admin-ask-channel-id"))


@router.message(AddChannel.waiting_chat_id)
async def add_channel_id(message: Message, i18n: TranslatorRunner, state: FSMContext) -> None:
    raw_value = (message.text or "").strip()
    normalized = normalize_channel_reference(raw_value)
    if not normalized:
        await message.answer(i18n.get("admin-ask-channel-id"))
        return

    await state.update_data(chat_id=normalized)
    await state.set_state(AddChannel.waiting_title)
    await message.answer(i18n.get("admin-ask-channel-title"))


@router.message(AddChannel.waiting_title)
async def add_channel_title(message: Message, db: Database, i18n: TranslatorRunner, state: FSMContext) -> None:
    data = await state.get_data()
    chat_id = str(data.get("chat_id", "")).strip()
    title = (message.text or "").strip()
    mandatory = bool(data.get("mandatory", False))

    if not chat_id:
        await state.clear()
        await message.answer(i18n.get("admin-ask-channel-id"))
        return

    await db.add_channel(chat_id, title, mandatory)
    await state.clear()
    await message.answer(i18n.get("admin-channel-added"))


@router.message(F.text.in_(REMOVE_MANDATORY_TEXTS) | F.text.in_(REMOVE_OPTIONAL_TEXTS))
async def start_remove_channel(message: Message, db: Database, i18n: TranslatorRunner, state: FSMContext) -> None:
    channels = await db.all_channels()
    if not channels:
        await message.answer(i18n.get("admin-no-channels"))
        return

    listing = "\n".join(f"{row['chat_id']} — {row['title'] or ''}" for row in channels)
    await state.set_state(RemoveChannel.waiting_chat_id)
    await message.answer(f"{i18n.get('admin-ask-channel-id')}\n\n{listing}")


@router.message(RemoveChannel.waiting_chat_id)
async def remove_channel(message: Message, db: Database, i18n: TranslatorRunner, state: FSMContext) -> None:
    await db.remove_channel(normalize_channel_reference((message.text or "").strip()))
    await state.clear()
    await message.answer(i18n.get("admin-channel-removed"))
