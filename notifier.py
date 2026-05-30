import os
import re
import requests
from datetime import datetime


def send_telegram(message: str) -> bool:
    token   = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("[notifier] Telegram not configured, skipping")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "HTML",
                  "disable_web_page_preview": False},
            timeout=10,
        )
        ok = r.status_code == 200
        if not ok:
            print(f"[notifier] Telegram error: {r.text}")
        return ok
    except Exception as e:
        print(f"[notifier] Telegram exception: {e}")
        return False


def send_slack(message: str) -> bool:
    token   = os.getenv("SLACK_BOT_TOKEN", "").strip()
    channel = os.getenv("SLACK_CHANNEL_ID", "").strip()
    if not token or not channel:
        print("[notifier] Slack not configured, skipping")
        return False
    try:
        r = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}"},
            json={"channel": channel, "text": message},
            timeout=10,
        )
        data = r.json()
        ok = data.get("ok", False)
        if not ok:
            print(f"[notifier] Slack error: {data.get('error', r.text)}")
        return ok
    except Exception as e:
        print(f"[notifier] Slack exception: {e}")
        return False


def notify_report_ready(
    geo: str,
    report_id: int,
    stats: dict,
    top_recommendations: list,
    team_lead: str = "",
    gdocs_url: str = "",
) -> None:
    """Send Telegram + Slack notification when pipeline report is ready."""
    app_url  = os.getenv("APP_URL", "http://localhost:5173").rstrip("/")
    report_url = f"{app_url}/report/{report_id}"

    urgent  = stats.get("urgent_count", 0)
    eternal = stats.get("eternal_count", 0)
    now     = datetime.now().strftime("%d.%m.%Y %H:%M")

    lines = [
        f"🗞 <b>Новый отчёт готов: {geo}</b>",
        f"📅 {now}",
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
        f"♾️ Вечные темы: {eternal}",
    ]

    if top_recommendations:
        lines.append("")
        lines.append("🏆 <b>Топ-5 к тесту:</b>")
        for rec in top_recommendations[:5]:
            rank  = rec.get("rank", "?")
            title = rec.get("angle_title", "")[:80]
            lines.append(f"{rank}. {title}")

    lines += [
        "",
        f'🔗 <a href="{report_url}">Открыть отчёт #{report_id}</a>',
    ]

    if gdocs_url:
        lines.append(f'📄 <a href="{gdocs_url}">Google Docs версия</a>')

    html_msg = "\n".join(lines)
    send_telegram(html_msg)

    # Slack — strip HTML tags, keep plain text
    plain = re.sub(r"<[^>]+>", "", html_msg)
    # Restore links in Slack mrkdwn format
    plain = re.sub(r'Открыть отчёт #(\d+)', f'<{report_url}|Открыть отчёт #{report_id}>', plain)
    if gdocs_url:
        plain = plain.replace("Google Docs версия", f"<{gdocs_url}|Google Docs версия>")
    send_slack(plain)
