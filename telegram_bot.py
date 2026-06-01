#!/usr/bin/env python3
"""
Telegram Bot — интерактивный интерфейс для AI-мониторинга инфоповодов.

Все запуски пайплайна идут через FastAPI (/api/run), поэтому отчёты
сохраняются в общую SQLite-базу и сразу видны на веб-сайте.

Команды:
  /start         — приветствие и список команд
  /help          — справка
  /run <GEO>     — запустить пайплайн для GEO (IN/BR/MX/RU/UA/BY/...)
  /run_all       — запустить для всех дефолтных GEO
  /geos          — список поддерживаемых GEO
  /last <GEO>    — последний отчёт по GEO из базы
  /status        — статус бота
"""

import asyncio
import os
import time
import threading
import requests as _http

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

from config import TELEGRAM_BOT_TOKEN, DEFAULT_GEOS

SUPPORTED_GEOS = ["IN", "BR", "MX", "RU", "UA", "BY", "KZ", "DE", "PL"]

# FastAPI runs on the same host — same container on Railway, localhost in dev
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

_running_jobs: dict[str, int] = {}   # geo → report_id


# ── API helpers ───────────────────────────────────────────────────────────────

def _api_run(geo: str, team_lead: str = "Telegram Bot") -> int:
    """POST /api/run → returns report_id."""
    resp = _http.post(f"{API_BASE}/api/run", json={
        "geo": geo,
        "use_mock": False,
        "team_lead": team_lead,
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["report_id"]


def _api_poll(report_id: int, timeout: int = 600, interval: int = 15) -> dict:
    """Poll GET /api/reports/{id} until status == done or error."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = _http.get(f"{API_BASE}/api/reports/{report_id}", timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data["status"] in ("done", "error"):
            return data
        time.sleep(interval)
    raise TimeoutError(f"Report {report_id} did not finish in {timeout}s")


def _api_last(geo: str) -> dict | None:
    """GET /api/reports?geo=X → return the most recent done report detail."""
    resp = _http.get(f"{API_BASE}/api/reports", params={"geo": geo}, timeout=15)
    resp.raise_for_status()
    reports = resp.json()
    done = [r for r in reports if r["status"] == "done"]
    if not done:
        return None
    report_id = done[0]["id"]
    detail = _http.get(f"{API_BASE}/api/reports/{report_id}", timeout=15)
    detail.raise_for_status()
    return detail.json()


# ── Summary formatter ─────────────────────────────────────────────────────────

def _format_summary(report: dict) -> str:
    """Compact summary matching the notifier.py format — stays well under 4096 chars."""
    from datetime import datetime as _dt

    geo       = report.get("geo", "?")
    report_id = report.get("id", "?")
    team_lead = report.get("team_lead") or ""
    stats     = report.get("stats", {})
    news_list = report.get("news", [])
    gdocs_url = report.get("gdocs_url") or ""

    app_url    = os.getenv("APP_URL", "").rstrip("/")
    report_url = f"{app_url}/report/{report_id}" if app_url else ""

    created_raw = report.get("created_at") or ""
    try:
        created = _dt.fromisoformat(created_raw).strftime("%d.%m.%Y %H:%M")
    except Exception:
        created = created_raw[:16]

    urgent  = sum(1 for n in news_list if n.get("urgency") == "urgent_48h")
    week    = sum(1 for n in news_list if n.get("urgency") == "week")
    eternal = sum(1 for n in news_list if n.get("urgency") == "eternal")

    lines = [
        f"🗞 <b>Новый отчёт готов: {geo}</b>",
        f"📅 {created}",
    ]
    if team_lead:
        lines.append(f"👤 Тимлид: {team_lead}")

    lines += [
        "",
        "📊 <b>Результаты:</b>",
        f"• {stats.get('total_news', 0)} инфоповодов",
        f"• {stats.get('total_angles', 0)} маркетинговых углов",
        f"• {stats.get('total_headlines', 0)} заголовков",
        "",
        f"🔥 Срочно (48ч): {urgent}",
        f"📅 На неделе: {week}",
        f"♾️ Вечные темы: {eternal}",
        "",
    ]

    if report_url:
        lines.append(f'🔗 <a href="{report_url}">Открыть отчёт #{report_id}</a>')
    if gdocs_url:
        lines.append(f'📄 <a href="{gdocs_url}">Google Docs версия</a>')

    return "\n".join(lines)


# ── Command handlers ──────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 <b>AI Мониторинг инфоповодов</b>\n\n"
        "Команды:\n"
        "/run <code>GEO</code> — запустить пайплайн (пример: <code>/run IN</code>)\n"
        "/run_all — запустить для всех дефолтных GEO\n"
        "/last <code>GEO</code> — последний отчёт из базы\n"
        "/geos — список поддерживаемых GEO\n"
        "/status — статус\n"
        "/help — справка",
        parse_mode=ParseMode.HTML,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 <b>Справка</b>\n\n"
        "<b>/run IN</b> — запустить AI-пайплайн для Индии:\n"
        "  1. Сбор новостей (RSS + Google News + Twitter)\n"
        "  2. Классификация Haiku → углы Sonnet → заголовки → риски → топ-5\n"
        "  Отчёт сразу виден на сайте и в БД.\n\n"
        f"Дефолтные GEO: {', '.join(DEFAULT_GEOS)}\n"
        f"Все поддерживаемые: {', '.join(SUPPORTED_GEOS)}",
        parse_mode=ParseMode.HTML,
    )


async def cmd_geos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = "\n".join(f"• <code>{g}</code>" for g in SUPPORTED_GEOS)
    await update.message.reply_text(
        f"🌍 <b>Поддерживаемые GEO:</b>\n{lines}", parse_mode=ParseMode.HTML
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if _running_jobs:
        jobs = ", ".join(
            f"<code>{g}</code> (report #{rid})" for g, rid in _running_jobs.items()
        )
        text = f"⚙️ <b>Сейчас выполняется:</b>\n{jobs}"
    else:
        text = "✅ Бот готов к работе. Активных задач нет."
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_run(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "❌ Укажи GEO. Пример: <code>/run IN</code>", parse_mode=ParseMode.HTML
        )
        return

    geo = context.args[0].upper()
    if geo not in SUPPORTED_GEOS:
        await update.message.reply_text(
            f"❌ Неизвестный GEO: <code>{geo}</code>\n"
            f"Доступные: {', '.join(SUPPORTED_GEOS)}",
            parse_mode=ParseMode.HTML,
        )
        return

    if geo in _running_jobs:
        rid = _running_jobs[geo]
        await update.message.reply_text(
            f"⚙️ Пайплайн для <code>{geo}</code> уже выполняется (report #{rid}).",
            parse_mode=ParseMode.HTML,
        )
        return

    await update.message.reply_text(
        f"🚀 Запускаю пайплайн для <b>{geo}</b> через API...\nЭто займёт ~5 минут.",
        parse_mode=ParseMode.HTML,
    )

    chat_id = update.effective_chat.id

    def _worker(geo: str):
        try:
            report_id = _api_run(geo)
            _running_jobs[geo] = report_id
            report = _api_poll(report_id)
            if report["status"] == "done":
                summary = _format_summary(report)
            else:
                summary = f"❌ Пайплайн завершился с ошибкой для <b>{geo}</b>."
        except Exception as exc:
            summary = f"❌ Ошибка для <b>{geo}</b>:\n<code>{exc}</code>"
        finally:
            _running_jobs.pop(geo, None)

        asyncio.run_coroutine_threadsafe(
            context.bot.send_message(chat_id, summary, parse_mode=ParseMode.HTML),
            context.application.loop,
        )

    threading.Thread(target=_worker, args=(geo,), daemon=True).start()


async def cmd_run_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    already = [g for g in DEFAULT_GEOS if g in _running_jobs]
    if already:
        await update.message.reply_text(
            f"⚙️ Уже запущено: {', '.join(already)}. Дождись завершения.",
            parse_mode=ParseMode.HTML,
        )
        return

    await update.message.reply_text(
        f"🌍 Запускаю пайплайн для: <b>{', '.join(DEFAULT_GEOS)}</b>",
        parse_mode=ParseMode.HTML,
    )

    chat_id = update.effective_chat.id

    def _worker_all():
        for geo in DEFAULT_GEOS:
            if geo in _running_jobs:
                continue
            try:
                report_id = _api_run(geo)
                _running_jobs[geo] = report_id
                report = _api_poll(report_id)
                summary = _format_summary(report) if report["status"] == "done" \
                    else f"❌ Ошибка пайплайна для <b>{geo}</b>."
            except Exception as exc:
                summary = f"❌ Ошибка для <b>{geo}</b>:\n<code>{exc}</code>"
            finally:
                _running_jobs.pop(geo, None)

            asyncio.run_coroutine_threadsafe(
                context.bot.send_message(chat_id, summary, parse_mode=ParseMode.HTML),
                context.application.loop,
            )

    threading.Thread(target=_worker_all, daemon=True).start()


async def cmd_last(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "❌ Укажи GEO. Пример: <code>/last IN</code>", parse_mode=ParseMode.HTML
        )
        return

    geo = context.args[0].upper()
    try:
        report = _api_last(geo)
    except Exception as exc:
        await update.message.reply_text(
            f"❌ Не удалось получить отчёт: <code>{exc}</code>", parse_mode=ParseMode.HTML
        )
        return

    if not report:
        await update.message.reply_text(
            f"📭 Нет завершённых отчётов для <code>{geo}</code>.", parse_mode=ParseMode.HTML
        )
        return

    await update.message.reply_text(_format_summary(report), parse_mode=ParseMode.HTML)


# ── App setup ─────────────────────────────────────────────────────────────────

async def _set_commands(app: Application) -> None:
    await app.bot.set_my_commands([
        BotCommand("start",   "Начало работы"),
        BotCommand("help",    "Справка"),
        BotCommand("run",     "Запустить пайплайн для GEO"),
        BotCommand("run_all", "Запустить для всех дефолтных GEO"),
        BotCommand("last",    "Последний отчёт по GEO"),
        BotCommand("geos",    "Список поддерживаемых GEO"),
        BotCommand("status",  "Статус бота"),
    ])


def run_bot() -> None:
    token = TELEGRAM_BOT_TOKEN
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан в .env")

    app = Application.builder().token(token).post_init(_set_commands).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("geos",    cmd_geos))
    app.add_handler(CommandHandler("status",  cmd_status))
    app.add_handler(CommandHandler("run",     cmd_run))
    app.add_handler(CommandHandler("run_all", cmd_run_all))
    app.add_handler(CommandHandler("last",    cmd_last))

    print(f"🤖 Telegram-бот запущен. API: {API_BASE}. Дефолтные GEO: {', '.join(DEFAULT_GEOS)}")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run_bot()
