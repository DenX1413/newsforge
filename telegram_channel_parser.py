"""
Парсер публичных Telegram-каналов через t.me/s/{channel}.
Не требует никаких ключей — работает с официальным веб-просмотром Telegram.
"""
import os
import re
import time
import requests
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Optional

# ── Дефолтные каналы по GEO ──────────────────────────────────────────────────

DEFAULT_CHANNELS: dict[str, list[str]] = {
    "RU": ["novosti_russia360", "ria_novosti_russya", "rossia_now"],
    "UA": ["ukraina_novosti", "tipichna_ukraine", "kievreal1"],
    "BY": ["belarusian_silovik", "minskctvby", "belteanews"],
    "KZ": ["tengrinews", "ztb_qaz", "zakonkz"],
    "PL": ["polsat_news"],
    "DE": ["spiegelnews"],
}

MAX_PER_CHANNEL = 8

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}


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
    url = f"https://t.me/s/{channel}"
    items = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            print(f"[tg_parser] @{channel}: HTTP {resp.status_code}")
            return []

        html = resp.text

        # Название канала
        title_match = re.search(r'<div class="tgme_channel_info_header_title"[^>]*>(.*?)</div>', html)
        chan_name = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else f"@{channel}"

        # Находим все сообщения
        messages = re.findall(
            r'<div class="tgme_widget_message_text js-message_text"[^>]*>(.*?)</div>'
            r'.*?<time datetime="([^"]+)"'
            r'.*?<a class="tgme_widget_message_date" href="(https://t\.me/[^"]+)"',
            html, re.DOTALL
        )

        for msg_html, dt_str, link in messages[:MAX_PER_CHANNEL]:
            # Убираем HTML теги
            text = re.sub(r"<[^>]+>", " ", msg_html)
            text = re.sub(r"\s+", " ", text).strip()

            if len(text) < 15:
                continue

            # Парсим дату
            pub = None
            try:
                pub = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            except Exception:
                pass

            if pub and pub < cutoff:
                continue

            # Заголовок = первые 150 символов
            lines = text.split(".")
            title_text = lines[0].strip()[:200] if lines else text[:150]
            desc = text[len(title_text):].strip()[:400]

            items.append(TelegramNewsItem(
                title        = title_text,
                source       = chan_name,
                description  = desc,
                original_url = link,
                published_at = pub,
                geo          = geo,
            ))

    except Exception as e:
        print(f"[tg_parser] @{channel}: ошибка — {e}")

    return items


def parse_telegram_channels(geo: str, days: int = 7) -> list[TelegramNewsItem]:
    channels = get_channels_for_geo(geo)
    if not channels:
        print(f"[tg_parser] Нет каналов для GEO={geo}")
        return []

    all_items: list[TelegramNewsItem] = []
    for channel in channels:
        items = _parse_channel(channel, geo, days)
        all_items.extend(items)
        print(f"[tg_parser] @{channel}: {len(items)} сообщений")
        time.sleep(0.3)

    print(f"[tg_parser] Итого для GEO={geo}: {len(all_items)} новостей из Telegram")
    return all_items
