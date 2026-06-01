#!/bin/bash
set -e

# Start Telegram bot in the background (runs from /app where config.py lives)
cd /app
python telegram_bot.py &
TGBOT_PID=$!
echo "🤖 Telegram bot started (PID $TGBOT_PID)"

# Start FastAPI in the foreground — Railway health checks hit this port
cd /app/backend
echo "🚀 Starting FastAPI on port ${PORT:-8000}"
exec uvicorn api:app --host 0.0.0.0 --port "${PORT:-8000}"
