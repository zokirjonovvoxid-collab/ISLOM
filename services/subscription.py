"""Helpers to check whether a user is subscribed to mandatory channels."""
from __future__ import annotations

import logging
from urllib.parse import urlparse

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from config import MAIN_CHANNEL
from db import get_db

DEFAULT_MANDATORY_CHANNELS = ["@uzbmediakino", "https://t.me/kinoman_000"]

NOT_MEMBER_STATUSES = {"left", "kicked"}
logger = logging.getLogger(__name__)


def normalize_channel_reference(raw: str) -> str:
    """Normalize Telegram channel references from admin input."""
    value = (raw or "").strip()
    if not value:
        return value

    if value.startswith(("http://", "https://")):
        parsed = urlparse(value)
        host = parsed.netloc.lower().replace("www.", "")
        if host in {"t.me", "telegram.me"}:
            path = parsed.path.lstrip("/")
            if path.startswith("joinchat/"):
                return path
            return f"@{path.lstrip('@')}" if path and not path.startswith("@") else path
        return value

    if value.startswith(("t.me/", "telegram.me/")):
        path = value.split("/", 1)[1].lstrip("/")
        if path.startswith("joinchat/"):
            return path
        return f"@{path.lstrip('@')}" if path and not path.startswith("@") else path

    if value.startswith("@"):
        return value

    return value


def _is_supported_subscription_target(chat_id: str) -> bool:
    value = normalize_channel_reference(chat_id)
    if not value:
        return False

    if value.startswith("joinchat/"):
        return True

    if value.startswith(("http://", "https://")):
        return True

    return value.startswith("@") or value.startswith("-100") or value.isdigit()


def _is_telegram_subscription_target(chat_id: str) -> bool:
    value = normalize_channel_reference(chat_id)
    return value.startswith("@") or value.startswith("-100") or value.isdigit()


def get_default_mandatory_channel_refs() -> list[str]:
    return [normalize_channel_reference(ref) for ref in DEFAULT_MANDATORY_CHANNELS if normalize_channel_reference(ref)]


async def _is_member(bot: Bot, chat_id: str, user_id: int) -> bool:
    normalized_chat_id = normalize_channel_reference(chat_id)
    try:
        member = await bot.get_chat_member(chat_id=normalized_chat_id, user_id=user_id)
    except TelegramBadRequest as exc:
        logger.debug("Subscription check failed for %s: %s", normalized_chat_id, exc)
        return False
    return member.status not in NOT_MEMBER_STATUSES


async def get_mandatory_channel_ids() -> list[str]:
    """Static main channel + any mandatory channels stored in the DB."""
    db = get_db()
    rows = await db.mandatory_channels()
    channel_ids: list[str] = []
    seen: set[str] = set()

    for chat_id in [normalize_channel_reference(MAIN_CHANNEL), *get_default_mandatory_channel_refs()]:
        if chat_id and chat_id not in seen:
            channel_ids.append(chat_id)
            seen.add(chat_id)

    for row in rows:
        chat_id = normalize_channel_reference(row["chat_id"])
        if chat_id and chat_id not in seen:
            channel_ids.append(chat_id)
            seen.add(chat_id)

    return channel_ids


async def get_unsubscribed_channels(bot: Bot, user_id: int) -> list[str]:
    """Return the list of mandatory subscription targets the user has not completed."""
    missing: list[str] = []
    for chat_id in await get_mandatory_channel_ids():
        if not _is_supported_subscription_target(chat_id):
            continue

        if _is_telegram_subscription_target(chat_id):
            if not await _is_member(bot, chat_id, user_id):
                missing.append(chat_id)
        else:
            missing.append(chat_id)

    return missing
