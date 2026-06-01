#!/usr/bin/env python3
"""
Telegram Bot — интерактивный интерфейс для AI-мониторинга инфоповодов.

Команды:
  /start         — приветствие и список команд
  /help          — справка
  /run <GEO>     — запустить пайплайн для GEO (IN/BR/MX/RU/UA/BY/...)
  /run_all       — запустить для всех дефолтных GEO
  /geos          — список поддерживаемых GEO
  /last <GEO>    — получить последний отчёт по GEO (краткий)
  /status        — статус бота
"""

import asyncio
import json
import os
import glob
import threading
from datetime import datetime

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

from config import TELEGRAM_BOT_TOKEN, DEFAULT_GEOS
from news_parser import NewsParser
from llm_processor import LLMProcessor
from report_generator import ReportGenerator
from notification_manager import NotificationManager

# GEOs that have RSS/Google News configured in news_parser.py
SUPPORTED_GEOS = ["IN", "BR", "MX", "RU", "UA", "BY", "KZ", "DE", "PL"]

_running_jobs: dict[str, bool] = {}


def _run_pipeline_sync(geo: str) -> dict | None:
    """Run pipeline synchronously (called inside a thread)."""
    from main import MonitoringPipeline
    pipeline = MonitoringPipeline()
    return pipeline.run_for_geo(geo)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "👋 <b>AI Мониторинг инфоповодов</b>\n\n"
        "Доступные команды:\n"
        "/run <code>GEO</code> — запустить пайплайн (например <code>/run IN</code>)\n"
        "/run_all — запустить для всех дефолтных GEO\n"
        "/last <code>GEO</code> — последний отчёт по GEO\n"
        "/geos — список поддерживаемых GEO\n"
        "/status — статус\n"
        "/help — справка"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 <b>Справка</b>\n\n"
        "<b>/run IN</b> — запустить полный AI-пайплайн для Индии:\n"
        "  1. Сбор новостей (RSS + Google News + Twitter)\n"
        "  2. Классификация (Haiku)\n"
        "  3. Генерация углов (Sonnet)\n"
        "  4. Генерация заголовков (Sonnet)\n"
        "  5. Оценка рисков (Sonnet)\n"
        "  6. Топ-5 рекомендаций с обоснованием\n\n"
        "Отчёт сохраняется в JSON и отправляется сюда кратким саммари.\n\n"
        f"Дефолтные GEO: {', '.join(DEFAULT_GEOS)}\n"
        f"Поддерживаемые GEO: {', '.join(SUPPORTED_GEOS)}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_geos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = "\n".join(f"• <code>{g}</code>" for g in SUPPORTED_GEOS)
    await update.message.reply_text(
        f"🌍 <b>Поддерживаемые GEO:</b>\n{lines}", parse_mode=ParseMode.HTML
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if _running_jobs:
        jobs = ", ".join(f"<code>{g}</code>" for g in _running_jobs)
        text = f"⚙️ <b>Сейчас выполняется:</b> {jobs}"
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
        await update.message.reply_text(
            f"⚙️ Пайплайн для <code>{geo}</code> уже запущен.", parse_mode=ParseMode.HTML
        )
        return

    await update.message.reply_text(
        f"🚀 Запускаю пайплайн для <b>{geo}</b>...\nЭто займёт ~5 минут.",
        parse_mode=ParseMode.HTML,
    )

    _running_jobs[geo] = True
    chat_id = update.effective_chat.id

    def _worker():
        try:
            report = _run_pipeline_sync(geo)
            if report:
                summary = _format_summary(report)
            else:
                summary = f"⚠️ Нет данных для <b>{geo}</b>. Проверь источники."
        except Exception as exc:
            summary = f"❌ Ошибка для <b>{geo}</b>:\n<code>{exc}</code>"
        finally:
            _running_jobs.pop(geo, None)

        asyncio.run_coroutine_threadsafe(
            context.bot.send_message(chat_id, summary, parse_mode=ParseMode.HTML),
            context.application.loop,
        )

    threading.Thread(target=_worker, daemon=True).start()


async def cmd_run_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    already = [g for g in DEFAULT_GEOS if g in _running_jobs]
    if already:
        await update.message.reply_text(
            f"⚙️ Уже запущено: {', '.join(already)}. Дождись завершения.",
            parse_mode=ParseMode.HTML,
        )
        return

    await update.message.reply_text(
        f"🌍 Запускаю пайплайн для всех GEO: <b>{', '.join(DEFAULT_GEOS)}</b>",
        parse_mode=ParseMode.HTML,
    )

    chat_id = update.effective_chat.id

    def _worker_all():
        for geo in DEFAULT_GEOS:
            if geo in _running_jobs:
                continue
            _running_jobs[geo] = True
            try:
                report = _run_pipeline_sync(geo)
                summary = _format_summary(report) if report else f"⚠️ Нет данных для <b>{geo}</b>."
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
    files = sorted(glob.glob(f"report_{geo}_*.json"))
    if not files:
        await update.message.reply_text(
            f"📭 Нет сохранённых отчётов для <code>{geo}</code>.", parse_mode=ParseMode.HTML
        )
        return

    latest = files[-1]
    try:
        with open(latest, encoding="utf-8") as f:
            report = json.load(f)
        summary = _format_summary(report)
        summary += f"\n\n📁 Файл: <code>{latest}</code>"
    except Exception as exc:
        summary = f"❌ Не удалось прочитать отчёт: <code>{exc}</code>"

    await update.message.reply_text(summary, parse_mode=ParseMode.HTML)


def _format_summary(report: dict) -> str:
    """Build a compact Telegram-friendly summary of a report."""
    h = report.get("header", {})
    stats = report.get("stats", {})
    b4 = report.get("block_4", {}).get("top_5_angles", [])
    b6 = report.get("block_6", {})

    urgent_count = len(b6.get("urgent", []))
    week_count   = len(b6.get("week", []))
    eternal_count = len(b6.get("eternal", []))

    lines = [
        f"📊 <b>Отчёт по инфоповодам: {h.get('geo','?')}</b>",
        f"📅 {h.get('generated_at','')[:10]}  |  👤 {h.get('responsible_lead','')}",
        f"📰 Новостей: {stats.get('total_news',0)}  |  "
        f"💡 Углов: {stats.get('total_angles',0)}  |  "
        f"📝 Заголовков: {stats.get('total_headlines',0)}",
        "",
        f"⏰ <b>Срочность:</b>  🔥 {urgent_count}  📅 {week_count}  ⏳ {eternal_count}",
    ]

    if h.get("previous_report_url"):
        lines.append(f"🔗 Предыдущий: <code>{h['previous_report_url']}</code>")

    if b4:
        lines.append("")
        lines.append("🏆 <b>Топ-5 рекомендаций:</b>")
        for rec in b4[:5]:
            rank = rec.get("rank", "?")
            title = rec.get("angle_title", "")[:80]
            reasoning = rec.get("reasoning", "")[:120]
            headlines = rec.get("headlines", [])
            lines.append(f"\n#{rank}. <b>{title}</b>")
            if reasoning:
                lines.append(f"   💬 {reasoning}")
            for hl in headlines[:2]:
                lines.append(f"   • {hl}")

    return "\n".join(lines)


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

    print(f"🤖 Telegram-бот запущен. Дефолтные GEO: {', '.join(DEFAULT_GEOS)}")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run_bot()
