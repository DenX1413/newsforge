from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class NewsItem(BaseModel):
    title: str
    source: str
    source_url: str
    source_type: str   # top_media | local_tabloid | google_news | twitter_trend | tiktok | telegram | forum
    date: datetime
    category: str
    description: str
    emotional_trigger: str
    urgency: str       # urgent_48h | week | eternal
    geo: str
    original_url: Optional[str] = None


class Angle(BaseModel):
    id: int
    news_id: str       # str(hash(news.title)) — for matching before DB save
    angle_title: str
    offer_connection: str
    target_pain: str
    creative_type: str  # news | emotional | investigation | personal_story
    priority: str       # A | B | C


class Headline(BaseModel):
    text: str
    angle_id: int
    format: str        # question | shock | number | quote | intrigue
    character_count: int


class RiskAssessment(BaseModel):
    news_id: str
    legal_risks: List[str]
    platform_ban_risk: str
    audience_negativity_risk: str
    reputation_risk: str
    expiry_date: str


class Recommendation(BaseModel):
    rank: int
    angle_id: int      # DB id (after save)
    angle_title: str
    news_title: str
    freshness: str
    trigger_strength: str
    offer_fit: str
    reasoning: str
