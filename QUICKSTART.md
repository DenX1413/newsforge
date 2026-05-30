# 🚀 Quick Start Guide

## 30 Seconds Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get your Anthropic API key
- Go to https://console.anthropic.com/
- Create new API key
- Copy it

### 3. Configure .env
```bash
# Edit .env file and add your key
ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Run demo (no API keys needed)
```bash
python demo.py
```

✅ You should see a formatted report output and `demo_report_RU.json` created.

---

## Run Full Pipeline

### With real API key
```bash
# Update .env with valid ANTHROPIC_API_KEY
python main.py
```

### What it does
1. Parses news from RSS feeds (RU, UA, BY)
2. Classifies with **Haiku** (fast)
3. Generates angles with **Sonnet** (quality)
4. Generates headlines with **Sonnet**
5. Assesses risks with **Sonnet**
6. Creates formatted JSON report
7. Sends to Slack/Telegram (if configured)

---

## Output

Reports are saved as:
- `report_RU_TIMESTAMP.json` - Full structured data
- `report_UA_TIMESTAMP.json` - For Ukraine
- `report_BY_TIMESTAMP.json` - For Belarus

---

## Notifications Setup (Optional)

### Slack
1. Create bot at https://api.slack.com/apps
2. Add "chat:write" permission
3. Copy bot token to `.env`
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C123...
```

### Telegram
1. Create bot via @BotFather
2. Copy token to `.env`
```
TELEGRAM_BOT_TOKEN=123:ABC...
TELEGRAM_CHAT_ID=12345
```

---

## Project Structure

```
Test/
├── main.py                 # Entry point - runs full pipeline
├── demo.py                 # Demo with mock data (run first)
├── config.py               # Configuration & constants
├── models.py               # Pydantic data models
├── news_parser.py          # Fetch & aggregate news
├── llm_processor.py        # Haiku classification + Sonnet generation
├── report_generator.py     # Format final reports
├── notification_manager.py # Send to Slack/Telegram
├── requirements.txt        # Dependencies
├── .env                    # Your API keys (KEEP SECRET!)
├── .env.example            # Template
├── README.md               # Full documentation
└── QUICKSTART.md           # This file
```

---

## Common Issues

### "ModuleNotFoundError: No module named 'anthropic'"
```bash
pip install -r requirements.txt
```

### "Unicode encoding error" (Windows)
```bash
# Run with:
$env:PYTHONIOENCODING='utf-8'; python main.py
```

### "Invalid API key"
- Check ANTHROPIC_API_KEY in .env
- Verify key starts with `sk-ant-`
- Get new key from console.anthropic.com

### "No news found"
- Check internet connection
- Verify RSS feeds are accessible
- Try different GEO

---

## Testing the Pipeline

### Test 1: Report generation (no API)
```bash
python demo.py
# Should show formatted report and save JSON
```

### Test 2: Real pipeline (needs API key)
```bash
python main.py
# Should fetch real news and generate full pipeline
# Creates report_RU_*, report_UA_*, report_BY_*
```

### Test 3: Check Slack/Telegram (optional)
- Configure credentials in .env
- Run `python main.py`
- Check your Slack channel / Telegram chat

---

## Report Structure

Each report contains 6 blocks:

**Block 1: Raw News** (10-20 items)
- Headlines, sources, categories, triggers

**Block 2: Marketing Angles** (20-30 items)
- News → Angle → Offer connections

**Block 3: Ad Headlines** (30-50 items)
- Question, shock, number, quote, intrigue formats

**Block 4: Testing Recommendations**
- Top-5 angles with 3 headlines each
- Prioritized for A/B testing

**Block 5: Risk Assessment**
- Legal, platform, reputation, audience risks
- Content expiry date

**Block 6: Urgency Summary**
- 🔥 Urgent (48h) vs ⏳ Eternal themes

---

## Model Strategy

| Task | Model | Why |
|------|-------|-----|
| News classification | **Haiku 4.5** | Fast + Cheap for repetitive tasks |
| Angle generation | **Sonnet 4.6** | Quality creative output |
| Headline generation | **Sonnet 4.6** | Marketing copywriting expertise |
| Risk assessment | **Sonnet 4.6** | Complex evaluation needed |

This hybrid approach:
- ✅ ~70% cheaper than Sonnet-only
- ✅ Faster classification with Haiku
- ✅ Quality guarantees with Sonnet

---

## Next Steps

1. ✅ Run `python demo.py` to see it work
2. ✅ Add your Anthropic API key to `.env`
3. ✅ Run `python main.py` for real pipeline
4. ✅ Configure Slack/Telegram for notifications
5. ✅ Schedule to run every 3-4 days (cron/Task Scheduler)
6. ✅ Integrate with Airtable for tracking (optional)

---

## Support

- 📖 Full docs: `README.md`
- 💬 Issues? Check `.env` first
- 🐛 Debug: Add `import logging; logging.basicConfig(level=logging.DEBUG)`
