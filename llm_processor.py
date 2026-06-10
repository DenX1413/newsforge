import hashlib
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
        """Haiku — classify all items in one batch request."""
        if not items:
            return items

        items_data = [
            {"index": i, "title": item.title, "text": item.description[:300]}
            for i, item in enumerate(items)
        ]
        prompt = (
            f"Classify {len(items_data)} news items. "
            f"Return a JSON array of exactly {len(items_data)} objects in the same order.\n\n"
            f"Items:\n{json.dumps(items_data, ensure_ascii=False)}\n\n"
            f"Return ONLY a JSON array (no markdown):\n"
            f'[{{"index":0,"category":"{"|".join(NEWS_CATEGORIES)}",'
            f'"emotional_trigger":"{"|".join(TRIGGERS)}",'
            f'"urgency":"urgent_48h|week|eternal"}}]'
        )
        try:
            resp = self.client.messages.create(
                model=HAIKU_MODEL, max_tokens=150 * len(items_data),
                messages=[{"role": "user", "content": prompt}],
            )
            results = _parse_json(resp.content[0].text)
            if isinstance(results, list):
                for r in results:
                    idx = r.get("index", -1)
                    if 0 <= idx < len(items):
                        items[idx].category          = r.get("category", "economy")
                        items[idx].emotional_trigger = r.get("emotional_trigger", "money")
                        items[idx].urgency           = r.get("urgency", "eternal")
        except Exception as e:
            print(f"[haiku] classify batch error: {e}")
            for item in items:
                item.category = "economy"
                item.emotional_trigger = "money"
                item.urgency = "eternal"

        return items

    # ── SONNET: angles ────────────────────────────────────────────────────────

    def generate_angles(
        self,
        items: List[NewsItem],
        geo: str,
        liked_examples: Optional[List[dict]] = None,
        vertical: str = "",
        keywords: str = "",
        language: str = "русский",
    ) -> List[Angle]:
        """Sonnet — generate 3 marketing angles per news item."""
        angles: List[Angle] = []
        angle_id = 1

        # Блок вертикали/ключевых слов
        vertical_block = ""
        if vertical:
            vertical_block += f"\nВертикаль/оффер: {vertical}."
        if keywords:
            vertical_block += f"\nКлючевые слова вертикали: {keywords}."
        if vertical_block:
            vertical_block += "\nГенерируй углы, которые можно связать с этим оффером."

        # Блок удачных примеров
        examples_block = ""
        if liked_examples:
            ex_lines = "\n".join(
                f"  - «{e['angle_title']}» → {e['offer_connection']}"
                for e in liked_examples[:4]
            )
            examples_block = (
                f"\n\nПримеры углов, которые ХОРОШО СРАБОТАЛИ ранее для {geo} "
                f"(используй похожий стиль):\n{ex_lines}"
            )

        batch_items = items[:10]
        items_data = [
            {
                "index": i,
                "title": item.title,
                "text": item.description[:300],
                "trigger": item.emotional_trigger,
            }
            for i, item in enumerate(batch_items)
        ]
        prompt = (
            f"News ({geo}): {len(items_data)} items. "
            f"For EACH item generate exactly 3 marketing angles.\n"
            f"{vertical_block}"
            f"{examples_block}\n\n"
            f"IMPORTANT: Write ALL text (angle_title, offer_connection, target_pain) in {language}.\n\n"
            f"Items:\n{json.dumps(items_data, ensure_ascii=False)}\n\n"
            f"Return ONLY a flat JSON array of ALL angles (no markdown), each object must include news_index:\n"
            f'[{{"news_index":0,"angle_title":"...","offer_connection":"...","target_pain":"...","creative_type":"news|emotional|investigation|personal_story"}}]'
        )
        try:
            resp = self.client.messages.create(
                model=SONNET_MODEL, max_tokens=700 * len(items_data),
                messages=[{"role": "user", "content": prompt}],
            )
            result = _parse_json(resp.content[0].text)
            if not isinstance(result, list):
                result = [result]
            for d in result:
                idx = d.get("news_index", 0)
                if 0 <= idx < len(batch_items):
                    item = batch_items[idx]
                    priority = "A" if item.emotional_trigger in ("money", "fear", "crisis") else "B"
                    angles.append(Angle(
                        id=angle_id,
                        news_id=hashlib.md5(item.title.encode()).hexdigest(),
                        angle_title=d.get("angle_title", ""),
                        offer_connection=d.get("offer_connection", ""),
                        target_pain=d.get("target_pain", ""),
                        creative_type=d.get("creative_type", "news"),
                        priority=priority,
                    ))
                    angle_id += 1
        except Exception as e:
            print(f"[sonnet] angles batch error: {e}")

        return angles

    # ── SONNET: headlines ─────────────────────────────────────────────────────

    def generate_headlines(self, angles: List[Angle], language: str = "русский") -> List[Headline]:
        """Sonnet — generate 4 ad headlines per angle (batched by 5)."""
        headlines: List[Headline] = []
        BATCH_SIZE = 5

        for batch_start in range(0, min(len(angles), 15), BATCH_SIZE):
            batch = angles[batch_start:batch_start + BATCH_SIZE]
            angles_data = [
                {
                    "index": i,
                    "angle_id": a.id,
                    "angle_title": a.angle_title,
                    "offer_connection": a.offer_connection,
                    "target_pain": a.target_pain,
                }
                for i, a in enumerate(batch)
            ]
            prompt = (
                f"For each of {len(batch)} marketing angles write 4 short ad headlines "
                f"with FOMO/intrigue. Max 90 chars each.\n"
                f"Formats: question / shock / number / quote / intrigue\n\n"
                f"IMPORTANT: Write headlines in {language}.\n\n"
                f"Angles:\n{json.dumps(angles_data, ensure_ascii=False)}\n\n"
                f"Return ONLY a JSON array (no markdown), one object per angle:\n"
                f'[{{"angle_index":0,"angle_id":0,"headlines":[{{"text":"...","format":"question"}}]}}]'
            )
            try:
                resp = self.client.messages.create(
                    model=SONNET_MODEL, max_tokens=500 * len(batch),
                    messages=[{"role": "user", "content": prompt}],
                )
                result = _parse_json(resp.content[0].text)
                if not isinstance(result, list):
                    result = [result]
                for item in result:
                    idx = item.get("angle_index", 0)
                    angle_id = item.get("angle_id") or (batch[idx].id if idx < len(batch) else None)
                    for h in item.get("headlines", []):
                        text = h.get("text", "").strip()
                        if text and angle_id:
                            headlines.append(Headline(
                                text=text,
                                angle_id=angle_id,
                                format=h.get("format", "intrigue"),
                                character_count=len(text),
                            ))
            except Exception as e:
                print(f"[sonnet] headlines batch error (start={batch_start}): {e}")

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
