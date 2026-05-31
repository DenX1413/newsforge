"""
Парсер Telegram-каналов для NewsForge.

Читает публичные каналы по GEO, возвращает список NewsItem-совместимых объектов.

Env vars (обязательны):
  TELEGRAM_API_ID
  TELEGRAM_API_HASH
  TELEGRAM_SESSION_STRING   ← получи через setup_telegram_session.py

Дополнительно (опционально):
  TELEGRAM_CHANNELS_RU=rian_ru,tass_agency,rbc_news
  TELEGRAM_CHANNELS_UA=ukrpravda_news,suspilne_ua
  ... и т.д. для любого GEO
"""
import os
import asyncio
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional

# ── Дефолтные каналы по GEO ──────────────────────────────────────────────────

DEFAULT_CHANNELS: dict[str, list[str]] = {
    "RU": ["rian_ru", "tass_agency", "rbc_news", "mash", "readovkaru"],
    "UA": ["ukrpravda_news", "suspilne_ua", "unian_news"],
    "BY": ["nexta_tv", "zerkalo_io"],
    "KZ": ["tengrinews", "kazinform_ru"],
    "PL": ["polsat_news", "tvn24"],
    "DE": ["spiegelnews", "derspiegel"],
}

MAX_MESSAGES_PER_CHANNEL = 10   # сколько последних сообщений брать с канала


@dataclass
class TelegramNewsItem:
    title: str
    source: str                      # название канала
    source_type: str = "telegram"
    description: str = ""
    original_url: str = ""
    published_at: Optional[datetime] = None
    geo: str = ""
    category: str = ""
    emotional_trigger: str = ""
    urgency: str = "week"


def _is_configured() -> bool:
    return bool(
        os.getenv("TELEGRAM_API_ID") and
        os.getenv("TELEGRAM_API_HASH") and
        os.getenv("TELEGRAM_SESSION_STRING")
    )


def get_channels_for_geo(geo: str) -> list[str]:
    """Возвращает список каналов для GEO из env или дефолтных."""
    env_key = f"TELEGRAM_CHANNELS_{geo.upper()}"
    env_val = os.getenv(env_key, "").strip()
    if env_val:
        return [c.strip().lstrip("@") for c in env_val.split(",") if c.strip()]
    return DEFAULT_CHANNELS.get(geo.upper(), [])


async def _fetch_channel(client, channel: str, geo: str,
                         days: int) -> list[TelegramNewsItem]:
    from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
    items = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    try:
        entity = await client.get_entity(f"@{channel}")
        chan_name = getattr(entity, "title", channel)

        async for msg in client.iter_messages(entity, limit=MAX_MESSAGES_PER_CHANNEL):
            if not msg.date or msg.date < cutoff:
                break
            text = (msg.text or "").strip()
            if len(text) < 30:           # слишком короткое — пропускаем
                continue

            # Первая строка = заголовок, остальное = описание
            lines = text.split("\n", 1)
            title = lines[0][:300].strip()
            desc  = lines[1][:500].strip() if len(lines) > 1 else ""

            url = f"https://t.me/{channel}/{msg.id}"
            items.append(TelegramNewsItem(
                title        = title,
                source       = chan_name,
                description  = desc,
                original_url = url,
                published_at = msg.date,
                geo          = geo,
            ))
    except Exception as e:
        print(f"[tg_parser] Ошибка канала @{channel}: {e}")
    return items


async def _parse_async(geo: str, days: int) -> list[TelegramNewsItem]:
    from telethon import TelegramClient
    from telethon.sessions import StringSession

    api_id      = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash    = os.getenv("TELEGRAM_API_HASH", "")
    session_str = os.getenv("TELEGRAM_SESSION_STRING", "")

    channels = get_channels_for_geo(geo)
    if not channels:
        print(f"[tg_parser] Нет каналов для GEO={geo}")
        return []

    all_items: list[TelegramNewsItem] = []
    async with TelegramClient(StringSession(session_str), api_id, api_hash) as client:
        for channel in channels:
            items = await _fetch_channel(client, channel, geo, days)
            all_items.extend(items)
            print(f"[tg_parser] @{channel}: {len(items)} сообщений")

    print(f"[tg_parser] Итого для GEO={geo}: {len(all_items)} новостей из Telegram")
    return all_items


def parse_telegram_channels(geo: str, days: int = 7) -> list[TelegramNewsItem]:
    """
    Синхронная обёртка. Возвращает пустой список если Telegram не настроен.
    """
    if not _is_configured():
        print("[tg_parser] Telegram API не настроен — пропускаем")
        return []

    try:
        return asyncio.run(_parse_async(geo, days))
    except Exception as e:
        print(f"[tg_parser] Ошибка: {e}")
        return []
