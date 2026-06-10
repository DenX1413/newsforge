import requests
from typing import Dict, Optional
from config import SLACK_BOT_TOKEN, SLACK_CHANNEL_ID, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import json


class NotificationManager:
    @staticmethod
    def send_slack_notification(message: str, file_data: Optional[Dict] = None) -> bool:
        """Send notification to Slack"""
        if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
            print("⚠️ Slack credentials not configured")
            return False

        try:
            # Send text message
            response = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
                json={
                    "channel": SLACK_CHANNEL_ID,
                    "text": message,
                },
            )

            result = response.json()
            if response.status_code == 200 and result.get("ok"):
                print("✅ Slack notification sent")
                return True
            else:
                print(f"❌ Slack error: {result.get('error', response.text)}")
                return False

        except Exception as e:
            print(f"❌ Slack error: {e}")
            return False

    @staticmethod
    def send_telegram_notification(message: str, file_data: Optional[Dict] = None) -> bool:
        """Send notification to Telegram"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("⚠️ Telegram credentials not configured")
            return False

        try:
            # Send text message
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML",
                },
            )

            if response.status_code == 200:
                print("✅ Telegram notification sent")
                return True
            else:
                print(f"❌ Telegram error: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False

    @staticmethod
    def send_notification(message: str, file_data: Optional[Dict] = None) -> Dict:
        """Send notification to all configured channels"""
        results = {
            "slack": NotificationManager.send_slack_notification(message, file_data),
            "telegram": NotificationManager.send_telegram_notification(message, file_data),
        }
        return results

    @staticmethod
    def send_report(report_text: str, report_json: Dict, geo: str) -> Dict:
        """Send full report to notification channels"""
        header = f"📊 Отчёт по инфоповодам: {geo}\n\n"
        message = header + report_text[:4000]  # Truncate for message

        return NotificationManager.send_notification(message, report_json)
