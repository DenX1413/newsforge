#!/usr/bin/env python3
"""
Demo script showing how to use the pipeline with mock data
Useful for testing without real news sources
"""

from datetime import datetime, timedelta
from models import NewsItem, Angle, Headline, RiskAssessment
from report_generator import ReportGenerator
from notification_manager import NotificationManager


def create_mock_news() -> list:
    """Create mock news items for demo"""
    return [
        NewsItem(
            title="ЦБ РФ повысит ключевую ставку на 0.5% в июне",
            source="РБК",
            source_url="https://www.rbc.ru",
            source_type="top_media",
            date=datetime.now() - timedelta(days=1),
            category="economy",
            description="Центральный банк России объявил о повышении ключевой ставки на 0.5% на своем следующем заседании совета директоров. Это может повлиять на курсы валют и стоимость кредитов.",
            emotional_trigger="money",
            urgency="urgent_48h",
            geo="RU",
            original_url="https://www.rbc.ru/news/...",
        ),
        NewsItem(
            title="Мировые акции растут на фоне снижения инфляции в США",
            source="Интерфакс",
            source_url="https://www.interfax.ru",
            source_type="top_media",
            date=datetime.now() - timedelta(days=2),
            category="economy",
            description="Глобальные индексы акций показывают рост после публикации данных о замедлении инфляции в Соединенных Штатах. Инвесторы становятся более оптимистичны.",
            emotional_trigger="opportunity",
            urgency="eternal",
            geo="RU",
            original_url="https://www.interfax.ru/news/...",
        ),
        NewsItem(
            title="Технологический стартап получил инвестиции в размере $50 млн",
            source="TechNews",
            source_url="https://technews.example.com",
            source_type="local_tabloid",
            date=datetime.now() - timedelta(hours=6),
            category="economy",
            description="Молодой российский стартап, разрабатывающий AI-решения, привлек внушительный раунд финансирования от иностранных инвесторов.",
            emotional_trigger="opportunity",
            urgency="urgent_48h",
            geo="RU",
            original_url="https://technews.example.com/news/...",
        ),
        NewsItem(
            title="Киноактер объявил о неожиданной роли в голливудском блокбастере",
            source="Кино.ру",
            source_url="https://kino.ru",
            source_type="social_media",
            date=datetime.now() - timedelta(hours=4),
            category="celebrity",
            description="Известный российский актер объявил о своем участии в долгожданном голливудском фильме. Новость вызвала бурную реакцию фанатов в социальных сетях.",
            emotional_trigger="trust",
            urgency="eternal",
            geo="RU",
            original_url="https://kino.ru/news/...",
        ),
    ]


def create_mock_angles() -> list:
    """Create mock angles for demo"""
    return [
        Angle(
            id=1,
            news_id="1234567890",
            angle_title="Укрепляй финансовую независимость - ставка идет вверх",
            offer_connection="Финансовые инструменты для защиты от инфляции",
            target_pain="Страх потерять сбережения из-за инфляции",
            creative_type="emotional",
            priority="A",
        ),
        Angle(
            id=2,
            news_id="1234567890",
            angle_title="Сейчас лучше взять кредит? Разбираемся в повышении ставок",
            offer_connection="Консультация финансового советника",
            target_pain="Неопределенность в финансовом планировании",
            creative_type="news",
            priority="A",
        ),
        Angle(
            id=3,
            news_id="0987654321",
            angle_title="Глобальный рост - твой шанс заработать",
            offer_connection="Инвестиционный портфель с акциями",
            target_pain="Упустить возможность для роста капитала",
            creative_type="investigation",
            priority="B",
        ),
    ]


def create_mock_headlines() -> list:
    """Create mock headlines for demo"""
    return [
        Headline(
            text="ЦБ повысит ставки: как это повлияет на ваш кошелек?",
            angle_id=1,
            format="question",
            character_count=52,
        ),
        Headline(
            text="Шокирующее изменение: ставки растут на 0.5% за одну ночь",
            angle_id=1,
            format="shock",
            character_count=56,
        ),
        Headline(
            text="3 способа защитить сбережения от инфляции прямо сейчас",
            angle_id=1,
            format="number",
            character_count=57,
        ),
        Headline(
            text="\"Это исторический момент\" - эксперты о новых ставках ЦБ",
            angle_id=2,
            format="quote",
            character_count=56,
        ),
        Headline(
            text="Если не знаешь про эти скрытые комиссии - срочно читай",
            angle_id=2,
            format="intrigue",
            character_count=55,
        ),
        Headline(
            text="Мировой рынок акций растет: упустишь ли ты выгоду?",
            angle_id=3,
            format="question",
            character_count=52,
        ),
    ]


def create_mock_risks() -> list:
    """Create mock risk assessments for demo"""
    return [
        RiskAssessment(
            news_id="1234567890",
            legal_risks=["Проверить цитаты ЦБ на точность", "Убедиться что не финансовый совет"],
            platform_ban_risk="low",
            audience_negativity_risk="medium",
            reputation_risk="low",
            expiry_date="48h",
        ),
        RiskAssessment(
            news_id="0987654321",
            legal_risks=["Проверить источники исследования рынка"],
            platform_ban_risk="low",
            audience_negativity_risk="low",
            reputation_risk="low",
            expiry_date="eternal",
        ),
    ]


def run_demo():
    """Run demo pipeline"""
    print("\n" + "="*70)
    print("🚀 AI NEWS MONITORING PIPELINE - DEMO")
    print("="*70 + "\n")

    # Create mock data
    print("📋 Preparing mock data...")
    news_items = create_mock_news()
    angles = create_mock_angles()
    headlines = create_mock_headlines()
    risks = create_mock_risks()

    print(f"   ✅ Created {len(news_items)} news items")
    print(f"   ✅ Created {len(angles)} angles")
    print(f"   ✅ Created {len(headlines)} headlines")
    print(f"   ✅ Created {len(risks)} risk assessments\n")

    # Generate report
    print("📊 Generating report...")
    report = ReportGenerator.generate_report(
        geo="RU",
        news_items=news_items,
        angles=angles,
        headlines=headlines,
        risks=risks,
        responsible_lead="Demo Team",
    )
    print("   ✅ Report generated\n")

    # Format as text
    print("📝 Formatting report...")
    report_text = ReportGenerator.format_report_text(report)
    print(report_text)

    # Save to file
    print("\n💾 Saving report to file...")
    import json
    with open("demo_report_RU.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("   ✅ Saved to demo_report_RU.json\n")

    # Demonstrate notification (requires credentials)
    print("📢 Testing notifications...")
    print("   (Skipped - requires Slack/Telegram credentials)")
    print("   To enable: configure SLACK_BOT_TOKEN and TELEGRAM_BOT_TOKEN in .env\n")

    print("="*70)
    print("✅ DEMO COMPLETE")
    print("="*70 + "\n")

    print("📚 Next steps:")
    print("1. Configure .env with your API keys")
    print("2. Test with: python main.py")
    print("3. Read README.md for detailed documentation\n")


if __name__ == "__main__":
    run_demo()
