"""
Одноразовый скрипт для получения Telegram StringSession.

Нужно:
  1. Зайди на https://my.telegram.org → API development tools
  2. Создай приложение, получи api_id и api_hash
  3. Запусти: python setup_telegram_session.py
  4. Введи номер телефона и код из Telegram
  5. Добавь в .env и Railway Variables:
       TELEGRAM_API_ID=...
       TELEGRAM_API_HASH=...
       TELEGRAM_SESSION_STRING=...
"""
import asyncio

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
except ImportError:
    print("Установи telethon: pip install telethon")
    exit(1)

api_id     = int(input("Введи api_id (число): ").strip())
api_hash   = input("Введи api_hash: ").strip()
phone      = input("Введи номер телефона (+7...): ").strip()

async def main():
    async with TelegramClient(StringSession(), api_id, api_hash) as client:
        await client.start(phone=phone)
        session_str = client.session.save()
        print("\n✅  Добавь в .env и Railway Variables:\n")
        print(f"TELEGRAM_API_ID={api_id}")
        print(f"TELEGRAM_API_HASH={api_hash}")
        print(f"TELEGRAM_SESSION_STRING={session_str}")
        print("\nЗатем перезапусти backend.")

asyncio.run(main())
