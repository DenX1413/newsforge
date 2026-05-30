# AI News Monitoring & Marketing Ideas Pipeline

Автоматизированная система для мониторинга инфоповодов и генерации маркетинговых идей под GEO.

## Архитектура

```
📰 NEWS AGGREGATION
├─ RSS Feeds
├─ Google News API
└─ Twitter/TikTok trends
        ↓
🏷️ CLASSIFICATION (Claude Haiku - fast)
├─ Category detection
├─ Emotional trigger extraction
└─ Urgency assessment
        ↓
💡 ANGLE GENERATION (Claude Sonnet - quality)
├─ Marketing angles (news → angle → offer)
├─ Target pain points
└─ Creative type selection
        ↓
📝 HEADLINE GENERATION (Claude Sonnet)
├─ 30-50 ad headlines
├─ Format selection (question/shock/number/quote/intrigue)
└─ Character count optimization
        ↓
⚠️ RISK ASSESSMENT (Claude Sonnet)
├─ Legal risks
├─ Platform ban risk
├─ Reputation risk
└─ Content expiry date
        ↓
📊 REPORT GENERATION
├─ Block 1: Raw inforeasons (10-20)
├─ Block 2: Angles & ideas (20-30)
├─ Block 3: Headlines (30-50)
├─ Block 4: Testing recommendations
├─ Block 5: Risk summary
└─ Block 6: Urgency classification
        ↓
📢 NOTIFICATIONS
├─ Slack
└─ Telegram
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
ANTHROPIC_API_KEY=sk-...
AIRTABLE_API_KEY=...
AIRTABLE_BASE_ID=...
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
DEFAULT_GEOS=RU,UA,BY
```

### 3. API Requirements

- **Anthropic API**: Claude Haiku + Sonnet access
- **News Sources**: RSS feeds configured per GEO (or Google News API)
- **Notifications**: Slack/Telegram bot tokens (optional)

## Usage

### Run Pipeline

```bash
python main.py
```

### Output

Pipeline generates:

1. **JSON Reports**: `report_GEO_TIMESTAMP.json`
   - Structured data for integration with Airtable
   - Full metadata for each block

2. **Console Output**: Real-time progress with emojis

3. **Notifications**: 
   - Slack: Formatted summary with top-5 recommendations
   - Telegram: HTML-formatted message

## Report Structure

### Header
- GEO
- Generation date
- Coverage period
- Responsible lead
- Source types

### Block 1: Raw Inforeasons (10-20)
```json
{
  "headline": "...",
  "source": "...",
  "source_type": "top_media|local_tabloid|twitter|tiktok|telegram|forum",
  "category": "economy|politics|social_media|celebrity|scandal|banks_taxes|fears",
  "emotional_trigger": "money|crisis|opportunity|fear|trust",
  "urgency": "urgent_48h|week|eternal"
}
```

### Block 2: Angles (20-30)
```json
{
  "id": 1,
  "angle_title": "...",
  "offer_connection": "...",
  "target_pain": "...",
  "creative_type": "news|emotional|investigation|personal_story",
  "priority": "A|B|C"
}
```

### Block 3: Headlines (30-50)
```json
{
  "text": "...",
  "angle_id": 1,
  "format": "question|shock|number|quote|intrigue",
  "character_count": 50
}
```

### Block 4: Testing Recommendations
Top-5 angles with:
- Justification (freshness, trigger strength, offer fit)
- 3 best headlines per angle
- A/B/C priority tier

### Block 5: Risks
- Legal risks
- Platform ban risk (high/medium/low)
- Audience negativity risk
- Reputation risk
- Content expiry time

### Block 6: Urgency Summary
- 🔥 Urgent (test within 48h)
- ⏳ Eternal themes

## Model Selection

- **Haiku 4.5**: News classification (fast, cheap)
- **Sonnet 4.6**: Content generation (quality, reasonable cost)

Split optimizes for:
- **Speed**: Haiku for repetitive classification
- **Quality**: Sonnet for creative angles/headlines
- **Cost**: ~70% cheaper than using Sonnet for everything

## Integration with Airtable

Tables structure (optional):
- `Inforeasons`: Raw news items
- `Angles`: Marketing angles
- `Headlines`: Generated headlines
- `GEOs`: Geography configuration
- `Tests/Results`: Campaign performance tracking

Report JSON maps directly to Airtable table fields.

## Scheduling

For automated runs every 3-4 days:

### Using cron (Linux/Mac)
```bash
0 9 * * 1,4 cd /path/to/project && python main.py
```

### Using Task Scheduler (Windows)
Create task running `python main.py` on schedule.

### Using APScheduler (Python)
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(pipeline.run_all_geos, 'interval', days=3)
scheduler.start()
```

## Customization

### Add News Sources

Edit `news_parser.py`:
```python
def parse_rss_feeds(self, geo: str):
    feeds = {
        "RU": ["https://feeds.example.com/news"],
        # Add more sources
    }
```

### Modify LLM Prompts

Edit `llm_processor.py` for custom classification/generation logic.

### Change Report Format

Edit `report_generator.py` for custom output structure.

## Error Handling

- Missing news sources: Skips and continues
- API failures: Retries with exponential backoff
- JSON parsing errors: Falls back to defaults

## Performance

Typical run times (per GEO):
- News aggregation: 5-10s
- Classification: 30-60s
- Angle generation: 1-2m
- Headline generation: 1-2m
- Risk assessment: 30-60s
- Report generation: 5-10s
- **Total: ~5-7 minutes per GEO**

## Troubleshooting

**No news found:**
- Check RSS feeds are accessible
- Verify news_coverage_days setting
- Test with direct RSS parser

**LLM errors:**
- Check ANTHROPIC_API_KEY is valid
- Verify quota limits not exceeded
- Review prompt formatting

**Notification failures:**
- Test Slack/Telegram bot tokens
- Verify channel IDs are correct
- Check firewall/VPN not blocking requests

## Future Enhancements

- [ ] Airtable direct integration
- [ ] Historical performance tracking
- [ ] Feedback loop for angle optimization
- [ ] Multi-language support
- [ ] Advanced filtering by keyword/sentiment
- [ ] Real-time streaming from social media
