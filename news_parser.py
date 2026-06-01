import feedparser
import requests
import urllib.parse
import os
import re
from datetime import datetime, timedelta
from typing import List
from models import NewsItem
from config import NEWS_COVERAGE_DAYS


class NewsParser:
    def __init__(self):
        self.coverage_days = NEWS_COVERAGE_DAYS
        self.cutoff_date = datetime.now() - timedelta(days=self.coverage_days)

    # ── RSS feeds ─────────────────────────────────────────────────────────────
    RSS_FEEDS = {
        "RU": [
            ("Lenta.ru",    "https://lenta.ru/rss/news",                    "top_media"),
            ("RIA Novosti", "https://ria.ru/export/rss2/archive/index.xml", "top_media"),
            ("TASS",        "https://tass.ru/rss/v2.xml",                   "top_media"),
            ("Interfax",    "https://www.interfax.ru/rss.asp",              "top_media"),
        ],
        "UA": [
            ("Ukrinform",   "https://www.ukrinform.ua/rss/block-lastnews",  "top_media"),
            ("Pravda UA",   "https://www.pravda.com.ua/rss/",               "top_media"),
            ("TSN",         "https://tsn.ua/rss/full.rss",                  "top_media"),
            ("Unian",       "https://rss.unian.net/site/news_ukr.rss",      "top_media"),
        ],
        "BY": [
            ("Sputnik BY",  "https://sputnik.by/export/rss2/index.xml",     "top_media"),
            ("Onliner.by",  "https://www.onliner.by/feed",                  "local_tabloid"),
        ],
        "KZ": [
            ("Sputnik KZ",  "https://ru.sputnik.kz/export/rss2/index.xml",  "top_media"),
            ("365info",     "https://365info.kz/feed/",                     "local_tabloid"),
        ],
        "DE": [
            ("Deutsche Welle", "https://rss.dw.com/rdf/rss-de-all",        "top_media"),
            ("Spiegel Online", "https://www.spiegel.de/schlagzeilen/index.rss", "top_media"),
        ],
        "PL": [
            ("TVN24",          "https://tvn24.pl/najnowsze.xml",            "top_media"),
            ("Onet",           "https://wiadomosci.onet.pl/.feed",          "top_media"),
        ],
        "IN": [
            ("NDTV",           "https://feeds.feedburner.com/ndtvnews-top-stories", "top_media"),
            ("The Hindu",      "https://www.thehindu.com/news/feeder/default.rss",  "top_media"),
            ("Times of India", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "top_media"),
            ("Economic Times", "https://economictimes.indiatimes.com/rssfeedstopstories.cms", "top_media"),
        ],
        "BR": [
            ("G1 Globo",       "https://g1.globo.com/rss/g1/",              "top_media"),
            ("UOL",            "https://rss.uol.com.br/feed/noticias.xml",  "top_media"),
            ("Folha",          "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml", "top_media"),
        ],
        "MX": [
            ("El Universal",   "https://www.eluniversal.com.mx/rss.xml",   "top_media"),
            ("Milenio",        "https://www.milenio.com/rss",               "top_media"),
            ("Proceso",        "https://www.proceso.com.mx/rss/",           "top_media"),
        ],
    }

    # ── Google News RSS queries per GEO ───────────────────────────────────────
    GOOGLE_NEWS_QUERIES = {
        "RU": [("ru", "RU", "экономика финансы россия"), ("ru", "RU", "банки налоги зарплаты россия")],
        "UA": [("uk", "UA", "економіка фінанси україна"), ("uk", "UA", "банки гроші україна")],
        "BY": [("ru", "BY", "беларусь экономика финансы"), ("ru", "BY", "беларусь зарплаты цены")],
        "KZ": [("ru", "KZ", "казахстан экономика тенге"), ("ru", "KZ", "казахстан банки цены")],
        "DE": [("de", "DE", "wirtschaft finanzen deutschland"), ("de", "DE", "krise inflation gehalt")],
        "PL": [("pl", "PL", "gospodarka finanse polska"), ("pl", "PL", "kryzys inflacja zarobki")],
        "IN": [("en", "IN", "india economy finance"), ("en", "IN", "india market banking money")],
        "BR": [("pt-BR", "BR", "economia brasil finanças"), ("pt-BR", "BR", "brasil banco juros renda")],
        "MX": [("es-419", "MX", "economía méxico finanzas"), ("es-419", "MX", "méxico banco dinero crisis")],
    }

    def _parse_date(self, entry) -> datetime:
        for attr in ("published_parsed", "updated_parsed"):
            val = getattr(entry, attr, None)
            if val:
                try:
                    return datetime(*val[:6])
                except Exception:
                    pass
        return datetime.now()

    def _clean_html(self, text: str) -> str:
        return re.sub(r"<[^>]+>", "", text or "").strip()

    def _make_news_item(self, title: str, source: str, source_url: str,
                        source_type: str, pub_date: datetime, description: str,
                        geo: str, original_url: str) -> NewsItem:
        return NewsItem(
            title=title,
            source=source,
            source_url=source_url,
            source_type=source_type,
            date=pub_date,
            category="economy",        # filled by LLM
            description=description,
            emotional_trigger="",      # filled by LLM
            urgency="",                # filled by LLM
            geo=geo,
            original_url=original_url,
        )

    # ── RSS parser ────────────────────────────────────────────────────────────
    def parse_rss_feeds(self, geo: str) -> List[NewsItem]:
        items: List[NewsItem] = []
        for source_name, feed_url, source_type in self.RSS_FEEDS.get(geo, []):
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:8]:
                    pub_date = self._parse_date(entry)
                    if pub_date < self.cutoff_date:
                        continue
                    title = self._clean_html(getattr(entry, "title", ""))
                    if not title:
                        continue
                    summary = self._clean_html(
                        getattr(entry, "summary", "") or getattr(entry, "description", "")
                    )[:400]
                    items.append(self._make_news_item(
                        title, source_name, feed_url, source_type,
                        pub_date, summary, geo,
                        getattr(entry, "link", ""),
                    ))
            except Exception as e:
                print(f"[parser] RSS error {feed_url}: {e}")
        return items

    # ── Google News RSS ───────────────────────────────────────────────────────
    def parse_google_news(self, geo: str) -> List[NewsItem]:
        """Fetch Google News RSS — no API key required."""
        items: List[NewsItem] = []
        for hl, gl, query in self.GOOGLE_NEWS_QUERIES.get(geo, []):
            try:
                encoded = urllib.parse.quote(query)
                url = f"https://news.google.com/rss/search?q={encoded}&hl={hl}&gl={gl}&ceid={gl}:{hl}"
                feed = feedparser.parse(url)
                for entry in feed.entries[:5]:
                    pub_date = self._parse_date(entry)
                    if pub_date < self.cutoff_date:
                        continue
                    title = self._clean_html(getattr(entry, "title", ""))
                    # Google News appends "- Source Name" — strip it
                    title = re.sub(r"\s*[-–]\s*\S.{2,35}$", "", title).strip()
                    if not title:
                        continue
                    summary = self._clean_html(getattr(entry, "summary", ""))[:400]
                    items.append(self._make_news_item(
                        title, "Google News", url, "google_news",
                        pub_date, summary, geo,
                        getattr(entry, "link", ""),
                    ))
            except Exception as e:
                print(f"[parser] Google News error {geo}: {e}")
        return items

    # ── Twitter / X API v2 ────────────────────────────────────────────────────
    def parse_twitter(self, geo: str) -> List[NewsItem]:
        """Fetch trending tweets via Twitter API v2 Bearer Token."""
        token = os.getenv("TWITTER_BEARER_TOKEN", "")
        if not token or token in ("test_token", ""):
            return []

        QUERIES = {
            "RU": "lang:ru (экономика OR кризис OR банки OR зарплата) -is:retweet",
            "UA": "lang:uk (економіка OR криза OR банки OR гроші) -is:retweet",
            "BY": "lang:ru (беларусь AND (кризис OR экономика OR зарплата)) -is:retweet",
            "KZ": "lang:ru (казахстан AND (кризис OR экономика OR тенге)) -is:retweet",
            "DE": "lang:de (wirtschaft OR krise OR inflation OR gehalt) -is:retweet",
            "PL": "lang:pl (gospodarka OR kryzys OR inflacja OR zarobki) -is:retweet",
        }
        query = QUERIES.get(geo)
        if not query:
            return []

        items: List[NewsItem] = []
        try:
            r = requests.get(
                "https://api.twitter.com/2/tweets/search/recent",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "query": query,
                    "max_results": 10,
                    "tweet.fields": "created_at,public_metrics",
                },
                timeout=10,
            )
            if r.status_code != 200:
                print(f"[parser] Twitter error {r.status_code}: {r.text[:200]}")
                return []

            for tweet in r.json().get("data", []):
                title = tweet.get("text", "")[:200]
                if not title:
                    continue
                created = tweet.get("created_at", "")
                try:
                    pub_date = datetime.fromisoformat(created.replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    pub_date = datetime.now()
                if pub_date < self.cutoff_date:
                    continue
                items.append(self._make_news_item(
                    title, "Twitter/X", "https://twitter.com", "twitter_trend",
                    pub_date, title, geo,
                    f"https://twitter.com/i/web/status/{tweet.get('id', '')}",
                ))
        except Exception as e:
            print(f"[parser] Twitter exception {geo}: {e}")
        return items

    # ── Aggregate ─────────────────────────────────────────────────────────────
    def aggregate_news(self, geo: str) -> List[NewsItem]:
        rss_items    = self.parse_rss_feeds(geo)
        google_items = self.parse_google_news(geo)
        twitter_items = self.parse_twitter(geo)

        all_items = rss_items + google_items + twitter_items

        # Deduplicate by first 60 chars of title
        seen: set = set()
        unique: List[NewsItem] = []
        for item in all_items:
            key = item.title[:60].lower()
            if key not in seen:
                seen.add(key)
                unique.append(item)

        result = sorted(unique, key=lambda x: x.date, reverse=True)[:20]
        print(
            f"[parser] {geo}: {len(result)} articles "
            f"(RSS:{len(rss_items)} GNews:{len(google_items)} Twitter:{len(twitter_items)})"
        )
        return result
