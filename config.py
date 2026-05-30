import os
from pathlib import Path
from dotenv import load_dotenv

# Всегда ищем .env в корне папки Test (на уровень выше config.py)
_env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
HAIKU_MODEL = "claude-haiku-4-5-20251001"
SONNET_MODEL = "claude-sonnet-4-6"

# Airtable
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

# News APIs
GOOGLE_NEWS_API_KEY = os.getenv("GOOGLE_NEWS_API_KEY")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Notifications
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Config
DEFAULT_GEOS = os.getenv("DEFAULT_GEOS", "RU,UA,BY").split(",")
NEWS_COVERAGE_DAYS = int(os.getenv("NEWS_COVERAGE_DAYS", "7"))
PIPELINE_RUN_INTERVAL_HOURS = int(os.getenv("PIPELINE_RUN_INTERVAL_HOURS", "72"))

# Categories
NEWS_CATEGORIES = [
    "economy",
    "politics",
    "social_media",
    "celebrity",
    "scandal",
    "banks_taxes",
    "fears",
]

# Emotional Triggers
TRIGGERS = ["money", "crisis", "opportunity", "fear", "trust"]

# Priority levels
PRIORITY_LEVELS = ["A", "B", "C"]

# Urgency types
URGENCY_TYPES = ["urgent", "eternal"]
