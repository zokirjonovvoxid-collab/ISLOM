"""Inline keyboard listing mandatory channels + a 'check' button."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner

from .callback_data import SubCheckCallback


def build_subscribe_url(channel_id: str) -> str:
    value = (channel_id or "").strip()
    if not value:
        return ""

    if value.startswith(("http://", "https://")):
        return value

    if value.startswith("@"):
        username = value.lstrip("@")
        return f"https://t.me/{username}"

    return f"https://t.me/{value}"


def subscribe_keyboard(channel_ids: list[str], i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for chat_id in channel_ids:
        builder.button(
            text=f"{i18n.get('sub-button')} {chat_id}",
            url=build_subscribe_url(chat_id),
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("sub-check-button"),
            callback_data=SubCheckCallback().pack(),
        )
    )
    return builder.as_markup()
