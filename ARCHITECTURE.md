# 🏗️ System Architecture

## Overview

AI News Monitoring Pipeline is a sophisticated system that automates the process of finding marketing opportunities in news events. It combines:
- **Data aggregation** from multiple news sources
- **AI classification** for rapid filtering
- **Creative generation** for marketing angles and headlines
- **Risk assessment** for compliance and reputation

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT SOURCES                                                   │
├─────────────────────────────────────────────────────────────────┤
│ • RSS Feeds (news.com, rbc.ru, interfax.ru, etc.)              │
│ • Google News API (filtered by keywords + GEO)                 │
│ • Twitter/X API (trend detection)                              │
│ • TikTok (viral content tracking)                              │
│ • Telegram channels (local news)                               │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ NEWS AGGREGATION & DEDUPLICATION                                │
├─────────────────────────────────────────────────────────────────┤
│ → Parse and extract: title, source, date, snippet               │
│ → Deduplicate by title similarity                               │
│ → Filter by GEO relevance                                       │
│ → Sort by recency (last 7 days)                                 │
│ → Result: 15-20 news items per GEO                              │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: CLASSIFICATION (Claude Haiku 4.5)                      │
├─────────────────────────────────────────────────────────────────┤
│ For each news item, extract:                                    │
│ • Category (economy / politics / celebrity / scandal / etc)     │
│ • Emotional trigger (money / crisis / opportunity / fear)       │
│ • Urgency level (urgent_48h / week / eternal)                   │
│                                                                  │
│ Cost: ~$0.001 per item (very cheap)                            │
│ Speed: ~1-2 items per second                                    │
│ Why Haiku: Classification is mechanical, low complexity         │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: ANGLE GENERATION (Claude Sonnet 4.6)                   │
├─────────────────────────────────────────────────────────────────┤
│ For top 10 news items, generate 3 angles each:                  │
│ • Angle title (compelling marketing hook)                       │
│ • How to connect to your offer                                  │
│ • Target audience pain point                                    │
│ • Creative type (news / emotional / investigation / story)      │
│                                                                  │
│ Result: 20-30 unique angles per GEO                            │
│ Cost: ~$0.01 per 3 angles                                       │
│ Speed: ~5-10 items per minute                                   │
│ Why Sonnet: Needs creative, marketing-savvy generation          │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: HEADLINE GENERATION (Claude Sonnet 4.6)                │
├─────────────────────────────────────────────────────────────────┤
│ For each angle, generate 3-5 headlines:                         │
│ • Question format ("How to...?")                                │
│ • Shock format ("Shocking news...")                             │
│ • Number format ("3 reasons...")                                │
│ • Quote format ("Expert says...")                               │
│ • Intrigue format ("Don't miss...")                             │
│                                                                  │
│ Result: 30-50 ad headlines per GEO                              │
│ Cost: ~$0.02 total                                              │
│ Speed: ~2-3 headlines per second                                │
│ Why Sonnet: High-quality copywriting is critical for ROAS       │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: RISK ASSESSMENT (Claude Sonnet 4.6)                    │
├─────────────────────────────────────────────────────────────────┤
│ For top 5 news items, evaluate:                                 │
│ • Legal risks (defamation, copyright, regulatory)               │
│ • Platform ban risk (high / medium / low)                       │
│ • Audience negativity risk                                      │
│ • Reputation risk                                               │
│ • Content expiry date (when will it be irrelevant?)             │
│                                                                  │
│ Cost: ~$0.01                                                    │
│ Speed: ~1 item per second                                       │
│ Why Sonnet: Nuanced risk evaluation requires judgment           │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ REPORT GENERATION                                               │
├─────────────────────────────────────────────────────────────────┤
│ Format output into 6 blocks:                                    │
│ Block 1: Raw news items (10-20)                                 │
│ Block 2: Marketing angles (20-30)                               │
│ Block 3: Ad headlines (30-50)                                   │
│ Block 4: Top-5 with recommendations                             │
│ Block 5: Risk summary                                           │
│ Block 6: Urgency classification                                 │
│                                                                  │
│ Output formats:                                                 │
│ • JSON (for Airtable integration)                               │
│ • Human-readable text                                           │
│ • Formatted tables                                              │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ NOTIFICATIONS & DISTRIBUTION                                    │
├─────────────────────────────────────────────────────────────────┤
│ • Slack: Formatted message with top-5 recommendations           │
│ • Telegram: HTML-formatted summary                              │
│ • JSON file: Full structured data                               │
│ • Airtable: Direct API integration (optional)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Architecture

### Core Modules

```
config.py
├── Load environment variables
├── Define constants
├── Model selection (Haiku vs Sonnet)
└── Category/trigger vocabularies

models.py
├── NewsItem (raw news)
├── Angle (marketing angle)
├── Headline (ad copy)
├── RiskAssessment (compliance)
└── Report (complete output)

news_parser.py
├── NewsParser.parse_rss_feeds()
├── NewsParser.fetch_google_news()
├── NewsParser.fetch_twitter_trends()
└── NewsParser.aggregate_news()

llm_processor.py
├── LLMProcessor.classify_news()      [Haiku]
├── LLMProcessor.generate_angles()    [Sonnet]
├── LLMProcessor.generate_headlines() [Sonnet]
└── LLMProcessor.assess_risks()       [Sonnet]

report_generator.py
├── ReportGenerator.generate_report()
└── ReportGenerator.format_report_text()

notification_manager.py
├── NotificationManager.send_slack_notification()
├── NotificationManager.send_telegram_notification()
└── NotificationManager.send_report()

main.py
├── MonitoringPipeline.run_for_geo()
├── MonitoringPipeline.run_all_geos()
└── MonitoringPipeline.save_reports()
```

---

## LLM Cost & Performance Analysis

### Cost Breakdown (per GEO run)

| Stage | Model | Operations | Cost |
|-------|-------|-----------|------|
| Classification | Haiku | 15 items × 200 tokens | $0.015 |
| Angle generation | Sonnet | 10 items × 3 angles × 500 tokens | $0.010 |
| Headline generation | Sonnet | 30 angles × 5 headlines × 400 tokens | $0.020 |
| Risk assessment | Sonnet | 5 items × 300 tokens | $0.005 |
| **TOTAL PER GEO** | | | **$0.050** |
| **3 GEOs** | | | **$0.150** |
| **Per week (2 runs)** | | | **$0.300** |
| **Per month** | | | **$1.20** |

### If using Sonnet only:
- Single run: $0.30 (6x more expensive)
- Per month: $7.20 (6x more expensive)

### Speed (per GEO)
- News aggregation: 10s
- Classification: 30s
- Angle generation: 1m
- Headline generation: 2m
- Risk assessment: 30s
- Report generation: 10s
- **Total: ~5 minutes per GEO**
- **3 GEOs: ~15 minutes**

---

## Integration Points

### Input APIs

```python
# News sources
- feedparser (RSS)
- google-news-api (Google News)
- tweepy (Twitter API v2)
- requests (custom APIs)

# Data storage
- Airtable API (optional)
- Google Docs API (optional)
```

### Output APIs

```python
# Notifications
- Slack Web API
- Telegram Bot API

# Storage
- JSON files (local)
- Airtable (database)
- Google Drive (optional)
```

---

## Database Schema (Airtable Optional)

```
Inforeasons
├── Title (text)
├── Source (text)
├── SourceType (select: top_media/local/twitter/tiktok/telegram/forum)
├── Date (date)
├── Category (select: economy/politics/celebrity/scandal/banks/fears)
├── Description (long text)
├── Trigger (select: money/crisis/opportunity/fear/trust)
├── Urgency (select: urgent_48h/week/eternal)
├── GEO (link to GEOs)
└── SourceURL (url)

Angles
├── Title (text)
├── NewsID (link to Inforeasons)
├── OfferConnection (long text)
├── TargetPain (long text)
├── CreativeType (select: news/emotional/investigation/story)
├── Priority (select: A/B/C)
└── Headlines (link to Headlines)

Headlines
├── Text (text)
├── AngleID (link to Angles)
├── Format (select: question/shock/number/quote/intrigue)
├── CharacterCount (number)
└── Status (select: pending/active/tested)

Tests/Results
├── AngleID (link to Angles)
├── HeadlineText (text)
├── DateTested (date)
├── Platform (select: Facebook/Instagram/TikTok/Telegram)
├── CTR (number)
├── CPA (currency)
├── Notes (long text)
└── Result (select: win/neutral/loss)
```

---

## Scheduling Architecture

### Option 1: APScheduler (Python)
```python
scheduler = BackgroundScheduler()
scheduler.add_job(pipeline.run_all_geos, 'cron', day_of_week='0,3')
scheduler.start()
```

### Option 2: Cron (Linux/Mac)
```bash
0 9 */3 * * python /path/to/main.py
```

### Option 3: Windows Task Scheduler
- Task: "Run news monitoring pipeline"
- Trigger: Every 3 days at 9 AM
- Action: `python main.py`

---

## Error Handling Strategy

```
News Aggregation
├─ Empty results? Log warning, continue
├─ API timeout? Retry with backoff
└─ Malformed feed? Skip and continue

LLM Processing
├─ Invalid JSON response? Use defaults
├─ API rate limit? Queue and retry
├─ Prompt failure? Log and skip item
└─ Token limit exceeded? Truncate text

Report Generation
├─ Missing data? Use empty blocks
├─ Formatting error? Fallback to basic format
└─ File write error? Log and retry

Notifications
├─ Slack unavailable? Log warning, continue
├─ Telegram failure? Try alternative channel
└─ API auth error? Alert user
```

---

## Security Considerations

1. **API Key Management**
   - Store in .env (gitignored)
   - Never commit credentials
   - Rotate keys periodically

2. **Data Privacy**
   - News content is public
   - Don't store user PII
   - Comply with platform ToS

3. **Rate Limiting**
   - Respect API rate limits
   - Implement exponential backoff
   - Cache responses where possible

4. **Content Compliance**
   - Risk assessment catches legal issues
   - Flag potentially harmful angles
   - Notify team of compliance risks

---

## Future Enhancements

### Phase 2
- [ ] Airtable bidirectional sync
- [ ] Historical performance tracking
- [ ] Feedback loop for angle optimization
- [ ] A/B test recommendations based on past results

### Phase 3
- [ ] Multi-language support (translate for different markets)
- [ ] Advanced NLP sentiment analysis
- [ ] Real-time social media streaming
- [ ] Competitive intelligence integration

### Phase 4
- [ ] Fine-tuned models for specific niches
- [ ] Predictive performance scoring
- [ ] Automated creative variation
- [ ] Cross-GEO theme aggregation
