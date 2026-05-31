"""
Парсер Telegram-каналов для NewsForge.

Читает публичные каналы через RSS (RSSHub) — без API-ключей и авторизации.
Работает для любого публичного канала.

Env vars (опционально):
  TELEGRAM_CHANNELS_RU=rian_ru,tass_agency,rbc_news
  TELEGRAM_CHANNELS_UA=ukrpravda_news,suspilne_ua
  TELEGRAM_CHANNELS_BY=nexta_tv,zerkalo_io
  TELEGRAM_CHANNELS_KZ=tengrinews,kazinform_ru
  RSSHUB_URL=https://rsshub.app   (или свой инстанс)
"""
import os
import time
import feedparser
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Optional

# ── Дефолтные каналы по GEO ──────────────────────────────────────────────────

DEFAULT_CHANNELS: dict[str, list[str]] = {
    "RU": ["rian_ru", "tass_agency", "rbc_news", "mash", "readovkaru"],
    "UA": ["ukrpravda_news", "suspilne_ua", "unian_news"],
    "BY": ["nexta_tv", "zerkalo_io"],
    "KZ": ["tengrinews", "kazinform_ru"],
    "PL": ["polsat_news"],
    "DE": ["spiegelnews"],
}

RSSHUB_BASE = os.getenv("RSSHUB_URL", "https://rsshub.app").rstrip("/")
MAX_PER_CHANNEL = 10


@dataclass
class TelegramNewsItem:
    title: str
    source: str
    source_type: str = "telegram"
    description: str = ""
    original_url: str = ""
    published_at: Optional[datetime] = None
    geo: str = ""


def get_channels_for_geo(geo: str) -> list[str]:
    env_val = os.getenv(f"TELEGRAM_CHANNELS_{geo.upper()}", "").strip()
    if env_val:
        return [c.strip().lstrip("@") for c in env_val.split(",") if c.strip()]
    return DEFAULT_CHANNELS.get(geo.upper(), [])


def _parse_channel(channel: str, geo: str, days: int) -> list[TelegramNewsItem]:
    """Парсит один канал через RSSHub RSS."""
    url = f"{RSSHUB_BASE}/telegram/channel/{channel}"
    items = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            print(f"[tg_rss] @{channel}: не удалось получить RSS")
            return []

        chan_name = feed.feed.get("title", f"@{channel}")

        for entry in feed.entries[:MAX_PER_CHANNEL]:
            # Парсим дату
            pub = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if pub and pub < cutoff:
                continue

            title = (entry.get("title") or "").strip()[:300]
            desc  = (entry.get("summary") or entry.get("description") or "").strip()[:500]
            link  = entry.get("link", f"https://t.me/{channel}")

            if len(title) < 10:
                continue

            items.append(TelegramNewsItem(
                title        = title,
                source       = chan_name,
                description  = desc,
                original_url = link,
                published_at = pub,
                geo          = geo,
            ))
    except Exception as e:
        print(f"[tg_rss] @{channel}: ошибка — {e}")

    return items


def parse_telegram_channels(geo: str, days: int = 7) -> list[TelegramNewsItem]:
    """Синхронная функция. Не требует никаких credentials."""
    channels = get_channels_for_geo(geo)
    if not channels:
        print(f"[tg_rss] Нет каналов для GEO={geo}")
        return []

    all_items: list[TelegramNewsItem] = []
    for channel in channels:
        items = _parse_channel(channel, geo, days)
        all_items.extend(items)
        print(f"[tg_rss] @{channel}: {len(items)} сообщений")
        time.sleep(0.5)   # небольшая пауза между запросами

    print(f"[tg_rss] Итого для GEO={geo}: {len(all_items)} новостей из Telegram")
    return all_items


def is_configured() -> bool:
    """Всегда True — RSS не требует авторизации."""
    return True
