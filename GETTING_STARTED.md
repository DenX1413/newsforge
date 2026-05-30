# 🎯 Getting Started Checklist

## Phase 1: Understand the System (5 min)

- [ ] Read `PROJECT_OVERVIEW.md` (what you got)
- [ ] Skim `README.md` (how it works)
- [ ] Look at `demo_report_RU.json` (sample output)

## Phase 2: Test Without API Keys (5 min)

```bash
# Make sure you're in C:\Users\kokok\Desktop\Test
cd "C:\Users\kokok\Desktop\Test"

# Set UTF-8 encoding (Windows)
$env:PYTHONIOENCODING='utf-8'

# Run demo
python demo.py
```

**Expected output:**
- Formatted report with 4 news items
- 3 marketing angles
- 6 ad headlines
- File saved: `demo_report_RU.json`

✅ If this works, the system is installed correctly.

---

## Phase 3: Get API Key (2 min)

1. Go to https://console.anthropic.com/
2. Sign in with your email
3. Click "Create API key"
4. Copy the key (starts with `sk-ant-`)
5. Keep it secret! Don't share with anyone

---

## Phase 4: Configure API Key (2 min)

1. Open `C:\Users\kokok\Desktop\Test\.env` in notepad
2. Find the line: `ANTHROPIC_API_KEY=test_key`
3. Replace with your key: `ANTHROPIC_API_KEY=sk-ant-v7X...`
4. Save the file
5. Keep `.env` secret - never commit to git!

---

## Phase 5: Test with Real News (5 min)

```bash
# Same encoding setup
$env:PYTHONIOENCODING='utf-8'

# Run real pipeline
python main.py
```

**What to expect:**
- 🚀 Starting pipeline...
- 📰 Step 1: Aggregating news...
- 🏷️ Step 2: Classifying news with Haiku...
- 💡 Step 3: Generating marketing angles with Sonnet...
- 📝 Step 4: Generating ad headlines with Sonnet...
- ⚠️ Step 5: Assessing risks with Sonnet...
- 📊 Step 6: Generating report...
- 📢 Step 7: Sending notifications...

**Files created:**
- `report_RU_TIMESTAMP.json` - Full report for Russia
- `report_UA_TIMESTAMP.json` - Full report for Ukraine
- `report_BY_TIMESTAMP.json` - Full report for Belarus

✅ If you see these files, it works!

---

## Phase 6: Review Output (5 min)

1. Open one of the `report_*.json` files
2. Look at the structure:
   - Block 1: Raw news items
   - Block 2: Marketing angles
   - Block 3: Ad headlines
   - Block 4: Top-5 recommendations
   - Block 5: Risk assessment
   - Block 6: Urgency classification

3. Ask: "Would my team find this useful?"

---

## Phase 7: Set Up Notifications (Optional, 5 min)

### Slack
1. Go to https://api.slack.com/apps
2. Create new app
3. Add "chat:write" scope
4. Generate bot token
5. Copy to `.env`: `SLACK_BOT_TOKEN=xoxb-...`
6. Copy channel ID to `.env`: `SLACK_CHANNEL_ID=C123...`

### Telegram
1. Chat with @BotFather on Telegram
2. Create bot: `/newbot`
3. Copy token to `.env`: `TELEGRAM_BOT_TOKEN=...`
4. Get your chat ID: send message to bot, check logs
5. Copy to `.env`: `TELEGRAM_CHAT_ID=...`

---

## Phase 8: Automate Runs (Optional, 5 min)

### Option A: Cron (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add line for every 3 days at 9 AM
0 9 */3 * * python /path/to/main.py
```

### Option B: Windows Task Scheduler
1. Open Task Scheduler (Windows key → "Task Scheduler")
2. New Task
3. Name: "News Monitoring Pipeline"
4. Trigger: Every 3 days at 9 AM
5. Action: Run `python main.py` in `C:\Users\kokok\Desktop\Test`

### Option C: Python Scheduler
```bash
# Will run forever with configured schedule
python scheduler.py
```

---

## Phase 9: Customize for Your Use Case (Varies)

### Add Custom News Sources
Edit `news_parser.py` → `parse_rss_feeds()`:
```python
feeds = {
    "RU": [
        "https://your-rss-feed.com/feed",
        # Add more sources
    ],
}
```

### Modify LLM Prompts
Edit `llm_processor.py` → each `generate_*()` method:
- Change emotional triggers list
- Modify what categories to detect
- Adjust creative type recommendations

### Change Report Format
Edit `report_generator.py` → `format_report_text()`:
- Add sections
- Change styling
- Include/exclude blocks

### Add Slack Integration
It's already in `notification_manager.py` - just configure `.env`

---

## Phase 10: Track Performance (Long Term)

### Simple Way (Spreadsheet)
1. Create `tracking.json`
2. Log which angles got tested
3. Log CTR/CPA results
4. Compare to future reports

### Advanced Way (Airtable)
1. Create tables for news, angles, headlines, tests
2. Modify `llm_processor.py` to write to Airtable
3. Track performance metrics
4. Optimize based on historical data

---

## Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| "demo.py shows nothing" | Set `$env:PYTHONIOENCODING='utf-8'` |
| "API key invalid" | Check key starts with `sk-ant-`, not typos |
| "No news found" | Check internet, verify RSS feeds accessible |
| "Unicode errors" | Use PowerShell on Windows, set UTF-8 |
| "Rate limit hit" | Wait a few minutes, try again |
| "JSON parse error" | Check internet connection, retry |

---

## Success Indicators

You're doing great if:

- ✅ `python demo.py` shows formatted report
- ✅ `python main.py` creates `report_RU.json` files
- ✅ Reports contain 20-30 angles and 30-50 headlines
- ✅ You can open JSON and see structured data
- ✅ Top-5 recommendations make sense for your business

---

## What to Do Next

### Day 1: Testing
- [ ] Run demo
- [ ] Add API key
- [ ] Run main pipeline
- [ ] Review outputs

### Day 2-3: Customization
- [ ] Modify for your GEOs
- [ ] Adjust news sources
- [ ] Test Slack/Telegram notifications
- [ ] Review one week of outputs

### Week 2: Automation
- [ ] Set up scheduler
- [ ] Configure Airtable (optional)
- [ ] Brief team on outputs
- [ ] Start testing angles

### Week 3+: Optimization
- [ ] Track angle performance
- [ ] Feedback to improve prompts
- [ ] Iterate on categories
- [ ] Expand to more GEOs

---

## Time Estimates

| Step | Time | Can Skip? |
|------|------|----------|
| Read overview | 5m | No |
| Test demo | 5m | No |
| Get API key | 2m | No |
| Configure .env | 2m | No |
| Test real pipeline | 5m | No |
| Review output | 5m | No |
| Set up notifications | 5m | Yes* |
| Automate runs | 5m | Yes* |
| Customize | 30m+ | Yes* |

**\* Optional but recommended for production use**

**Total time to working system: ~30 minutes**

---

## Support

- 📖 Full docs: `README.md`
- 🏗️ Architecture: `ARCHITECTURE.md`
- 📋 Overview: `PROJECT_OVERVIEW.md`
- ❓ Questions: Check the docs first

---

**You're all set! Start with Step 1. 🚀**
