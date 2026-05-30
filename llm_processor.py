import json
import re
from typing import List, Optional
from anthropic import Anthropic
from config import HAIKU_MODEL, SONNET_MODEL, NEWS_CATEGORIES, TRIGGERS
from models import NewsItem, Angle, Headline, RiskAssessment


def _parse_json(raw: str):
    """Strip markdown fences and parse JSON."""
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    return json.loads(cleaned)


class LLMProcessor:
    def __init__(self):
        self.client = Anthropic()

    # ── HAIKU: classify ───────────────────────────────────────────────────────

    def classify_news(self, items: List[NewsItem]) -> List[NewsItem]:
        """Haiku — classify category, trigger, urgency for each news item."""
        classified = []
        for item in items:
            prompt = (
                f"Classify this news:\nTitle: {item.title}\nText: {item.description[:300]}\n\n"
                f"Return ONLY valid JSON (no markdown):\n"
                f'{{"category": "{"|".join(NEWS_CATEGORIES)}", '
                f'"emotional_trigger": "{"|".join(TRIGGERS)}", '
                f'"urgency": "urgent_48h|week|eternal"}}'
            )
            try:
                resp = self.client.messages.create(
                    model=HAIKU_MODEL, max_tokens=120,
                    messages=[{"role": "user", "content": prompt}],
                )
                data = _parse_json(resp.content[0].text)
                item.category          = data.get("category", "economy")
                item.emotional_trigger = data.get("emotional_trigger", "money")
                item.urgency           = data.get("urgency", "eternal")
            except Exception as e:
                print(f"[haiku] classify error: {e}")
                item.category = "economy"
                item.emotional_trigger = "money"
                item.urgency = "eternal"
            classified.append(item)
        return classified

    # ── SONNET: angles ────────────────────────────────────────────────────────

    def generate_angles(
        self,
        items: List[NewsItem],
        geo: str,
        liked_examples: Optional[List[dict]] = None,
    ) -> List[Angle]:
        """Sonnet — generate 3 marketing angles per news item.
        liked_examples: list of {"angle_title", "offer_connection"} from past liked angles.
        """
        angles: List[Angle] = []
        angle_id = 1

        # Build "what worked before" block once, reuse in all prompts
        examples_block = ""
        if liked_examples:
            ex_lines = "\n".join(
                f"  - «{e['angle_title']}» → {e['offer_connection']}"
                for e in liked_examples[:4]
            )
            examples_block = (
                f"\n\nПримеры углов, которые ХОРОШО СРАБОТАЛИ ранее для {geo} "
                f"(команда поставила лайк — используй похожий стиль и тональность):\n"
                f"{ex_lines}"
            )

        for item in items[:10]:
            prompt = (
                f"News ({geo}): \"{item.title}\"\n{item.description[:300]}\n\n"
                f"Generate exactly 3 marketing angles that connect this news to offers.\n"
                f"Emotional trigger: {item.emotional_trigger}"
                f"{examples_block}\n\n"
                f"Return ONLY a JSON array (no markdown):\n"
                f'[{{"angle_title":"...","offer_connection":"...","target_pain":"...","creative_type":"news|emotional|investigation|personal_story"}}]'
            )
            try:
                resp = self.client.messages.create(
                    model=SONNET_MODEL, max_tokens=700,
                    messages=[{"role": "user", "content": prompt}],
                )
                result = _parse_json(resp.content[0].text)
                if not isinstance(result, list):
                    result = [result]
                for d in result:
                    priority = "A" if item.emotional_trigger in ("money", "fear", "crisis") else "B"
                    angles.append(Angle(
                        id=angle_id,
                        news_id=str(hash(item.title)),
                        angle_title=d.get("angle_title", ""),
                        offer_connection=d.get("offer_connection", ""),
                        target_pain=d.get("target_pain", ""),
                        creative_type=d.get("creative_type", "news"),
                        priority=priority,
                    ))
                    angle_id += 1
            except Exception as e:
                print(f"[sonnet] angles error for '{item.title[:40]}': {e}")

        return angles

    # ── SONNET: headlines ─────────────────────────────────────────────────────

    def generate_headlines(self, angles: List[Angle]) -> List[Headline]:
        """Sonnet — generate 4 ad headlines per angle (up to 15 angles)."""
        headlines: List[Headline] = []

        for angle in angles[:15]:
            prompt = (
                f"Marketing angle: \"{angle.angle_title}\"\n"
                f"Offer: {angle.offer_connection}\n"
                f"Audience pain: {angle.target_pain}\n\n"
                f"Write 4 short ad headlines with FOMO/intrigue. Max 90 chars each.\n"
                f"Formats: question / shock / number / quote / intrigue\n\n"
                f"Return ONLY a JSON array (no markdown):\n"
                f'[{{"text":"...","format":"question"}}]'
            )
            try:
                resp = self.client.messages.create(
                    model=SONNET_MODEL, max_tokens=500,
                    messages=[{"role": "user", "content": prompt}],
                )
                result = _parse_json(resp.content[0].text)
                if not isinstance(result, list):
                    result = [result]
                for d in result:
                    text = d.get("text", "").strip()
                    if text:
                        headlines.append(Headline(
                            text=text,
                            angle_id=angle.id,
                            format=d.get("format", "intrigue"),
                            character_count=len(text),
                        ))
            except Exception as e:
                print(f"[sonnet] headlines error for angle {angle.id}: {e}")

        return headlines

    # ── SONNET: risks ─────────────────────────────────────────────────────────

    def assess_risks(self, items: List[NewsItem]) -> List[RiskAssessment]:
        """Sonnet — assess legal, platform, and reputation risks (top 5 items)."""
        risks: List[RiskAssessment] = []

        for item in items[:5]:
            prompt = (
                f"News: \"{item.title}\" (category: {item.category})\n\n"
                f"Assess marketing risks for using this news in ads.\n"
                f"Return ONLY JSON (no markdown):\n"
                f'{{"legal_risks":["..."],"platform_ban_risk":"high|medium|low",'
                f'"audience_negativity_risk":"high|medium|low","reputation_risk":"high|medium|low",'
                f'"expiry_date":"24h|48h|week|eternal"}}'
            )
            try:
                resp = self.client.messages.create(
                    model=SONNET_MODEL, max_tokens=300,
                    messages=[{"role": "user", "content": prompt}],
                )
                d = _parse_json(resp.content[0].text)
                risks.append(RiskAssessment(
                    news_id=str(hash(item.title)),
                    legal_risks=d.get("legal_risks", []),
                    platform_ban_risk=d.get("platform_ban_risk", "low"),
                    audience_negativity_risk=d.get("audience_negativity_risk", "low"),
                    reputation_risk=d.get("reputation_risk", "low"),
                    expiry_date=d.get("expiry_date", "eternal"),
                ))
            except Exception as e:
                print(f"[sonnet] risks error: {e}")

        return risks

    # ── SONNET: recommendations (Block 4) ─────────────────────────────────────

    def generate_recommendations(
        self,
        angles: List[Angle],
        news_items: List[NewsItem],
    ) -> List[dict]:
        """Sonnet — select top-5 angles with detailed reasoning."""
        news_map = {str(hash(n.title)): n for n in news_items}

        angles_data = []
        for a in angles[:30]:
            news = news_map.get(a.news_id)
            angles_data.append({
                "id": a.id,
                "angle_title": a.angle_title[:120],
                "offer_connection": a.offer_connection[:100],
                "target_pain": a.target_pain[:80],
                "creative_type": a.creative_type,
                "priority": a.priority,
                "news_title": news.title[:100] if news else "",
                "news_urgency": news.urgency if news else "eternal",
                "news_trigger": news.emotional_trigger if news else "money",
                "news_date": news.date.strftime("%d.%m.%Y") if news else "",
                "news_category": news.category if news else "",
            })

        prompt = (
            f"You are a performance marketing strategist. Analyze {len(angles_data)} marketing angles "
            f"and select exactly TOP 5 for immediate A/B testing, ranked 1-5 by expected performance.\n\n"
            f"Criteria: freshness (urgent_48h > week > eternal), trigger strength (fear/money/crisis = strongest), offer fit.\n\n"
            f"Angles:\n{json.dumps(angles_data, ensure_ascii=False)}\n\n"
            f"Return ONLY JSON array, exactly 5 items (no markdown):\n"
            f'[{{"rank":1,"angle_id":0,"angle_title":"...","news_title":"...",'
            f'"freshness":"reason in Russian","trigger_strength":"reason in Russian",'
            f'"offer_fit":"reason in Russian","reasoning":"overall reason in Russian"}}]'
        )

        try:
            resp = self.client.messages.create(
                model=SONNET_MODEL, max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            result = _parse_json(resp.content[0].text)
            if not isinstance(result, list):
                result = [result]
            return result[:5]
        except Exception as e:
            print(f"[sonnet] recommendations error: {e}")
            top = [a for a in angles if a.priority == "A"][:5]
            return [
                {
                    "rank": i + 1,
                    "angle_id": a.id,
                    "angle_title": a.angle_title,
                    "news_title": (news_map[a.news_id].title if a.news_id in news_map else ""),
                    "freshness": "Высокая",
                    "trigger_strength": "Приоритет A",
                    "offer_fit": "Хорошая связь с оффером",
                    "reasoning": "Автоматически выбран по приоритету A",
                }
                for i, a in enumerate(top)
            ]
