from datetime import datetime
from typing import List, Dict
from models import NewsItem, Angle, Headline, RiskAssessment


class ReportGenerator:
    @staticmethod
    def generate_report(
        geo: str,
        news_items: List[NewsItem],
        angles: List[Angle],
        headlines: List[Headline],
        risks: List[RiskAssessment],
        responsible_lead: str = "Team Lead",
    ) -> Dict:
        """Generate comprehensive report"""

        # Block 1: Raw inforeasons (10-20 items)
        block_1 = {
            "title": "Block 1. Сырые инфоповоды",
            "items": [
                {
                    "headline": item.title,
                    "source": item.source,
                    "source_url": item.source_url,
                    "source_type": item.source_type,
                    "date": item.date.isoformat(),
                    "category": item.category,
                    "description": item.description,
                    "emotional_trigger": item.emotional_trigger,
                    "urgency": item.urgency,
                }
                for item in news_items[:20]
            ],
        }

        # Block 2: Angles and ideas (20-30)
        angles_by_news = {}
        for angle in angles:
            if angle.news_id not in angles_by_news:
                angles_by_news[angle.news_id] = []
            angles_by_news[angle.news_id].append(angle)

        block_2 = {
            "title": "Block 2. Углы и идеи",
            "items": [
                {
                    "id": angle.id,
                    "news_id": angle.news_id,
                    "angle_title": angle.angle_title,
                    "offer_connection": angle.offer_connection,
                    "target_pain": angle.target_pain,
                    "creative_type": angle.creative_type,
                    "priority": angle.priority,
                }
                for angle in angles[:30]
            ],
        }

        # Block 3: Headlines (30-50)
        block_3 = {
            "title": "Block 3. Заголовки",
            "grouped_by_angle": {},
        }

        for headline in headlines:
            if headline.angle_id not in block_3["grouped_by_angle"]:
                block_3["grouped_by_angle"][headline.angle_id] = []
            block_3["grouped_by_angle"][headline.angle_id].append(
                {
                    "text": headline.text,
                    "angle_id": headline.angle_id,
                    "format": headline.format,
                    "character_count": headline.character_count,
                }
            )

        # Block 4: Testing recommendations
        top_5_angles = sorted(angles[:5], key=lambda x: x.priority)
        block_4 = {
            "title": "Block 4. Рекомендации к тесту",
            "top_5_angles": [
                {
                    "id": angle.id,
                    "angle_title": angle.angle_title,
                    "reasoning": f"Priority: {angle.priority}, Trigger: соответствует целевой аудитории",
                    "headlines": [
                        h.text
                        for h in headlines
                        if h.angle_id == angle.id
                    ][:3],
                }
                for angle in top_5_angles
            ],
        }

        # Block 5: Risks
        block_5 = {
            "title": "Block 5. Риски",
            "items": [
                {
                    "news_id": risk.news_id,
                    "legal_risks": risk.legal_risks,
                    "platform_ban_risk": risk.platform_ban_risk,
                    "audience_negativity_risk": risk.audience_negativity_risk,
                    "reputation_risk": risk.reputation_risk,
                    "expiry_date": risk.expiry_date,
                }
                for risk in risks
            ],
        }

        # Block 6: Urgency summary
        urgent_items = [item for item in news_items if item.urgency == "urgent_48h"]
        eternal_items = [item for item in news_items if item.urgency == "eternal"]

        block_6 = {
            "title": "Block 6. Срочность",
            "urgent": [{"headline": item.title, "urgency": "🔥 Срочно (48ч)"} for item in urgent_items],
            "eternal": [
                {"headline": item.title, "urgency": "⏳ Вечная тема"}
                for item in eternal_items
            ],
        }

        # Compile full report
        report = {
            "header": {
                "geo": geo,
                "generated_at": datetime.now().isoformat(),
                "coverage_days": 7,
                "responsible_lead": responsible_lead,
                "source_types": list(set(item.source_type for item in news_items)),
            },
            "block_1": block_1,
            "block_2": block_2,
            "block_3": block_3,
            "block_4": block_4,
            "block_5": block_5,
            "block_6": block_6,
            "stats": {
                "total_news": len(news_items),
                "total_angles": len(angles),
                "total_headlines": len(headlines),
                "total_risks_assessed": len(risks),
            },
        }

        return report

    @staticmethod
    def format_report_text(report: Dict) -> str:
        """Format report as readable text"""
        text = f"""
╔══════════════════════════════════════════════════════════╗
║          AI МОНИТОРИНГ ИНФОПОВОДОВ - {report['header']['geo']}           ║
╚══════════════════════════════════════════════════════════╝

📅 Дата: {report['header']['generated_at'][:10]}
👤 Ответственный: {report['header']['responsible_lead']}
📊 Период покрытия: последние {report['header']['coverage_days']} дней

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📰 БЛОК 1: СЫРЫЕ ИНФОПОВОДЫ ({len(report['block_1']['items'])} штук)

"""
        for i, item in enumerate(report["block_1"]["items"][:10], 1):
            text += f"{i}. {item['headline'][:50]}...\n"
            text += f"   📌 Источник: {item['source_type']} | {item['category']}\n"
            text += f"   ⚡ Триггер: {item['emotional_trigger']} | ⏱️ {item['urgency']}\n\n"

        text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"\n📌 БЛОК 4: ТОП-5 РЕКОМЕНДАЦИЙ К ТЕСТУ\n\n"

        for item in report["block_4"]["top_5_angles"]:
            text += f"💡 ID {item['id']}: {item['angle_title']}\n"
            text += f"   Обоснование: {item['reasoning']}\n"
            text += f"   Заголовки:\n"
            for headline in item["headlines"]:
                text += f"     • {headline}\n"
            text += "\n"

        text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"\n⏰ СРОЧНОСТЬ\n\n"
        text += f"🔥 Срочно (48ч): {len(report['block_6']['urgent'])} новостей\n"
        text += f"⏳ Вечные темы: {len(report['block_6']['eternal'])} новостей\n"

        text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"\n📊 СТАТИСТИКА\n"
        text += f"  • Обработано новостей: {report['stats']['total_news']}\n"
        text += f"  • Сгенерировано углов: {report['stats']['total_angles']}\n"
        text += f"  • Сгенерировано заголовков: {report['stats']['total_headlines']}\n"
        text += f"  • Оценено рисков: {report['stats']['total_risks_assessed']}\n"

        return text
