#!/usr/bin/env python3
"""
AI News Monitoring & Marketing Ideas Pipeline
Orchestrates news collection, classification, angle generation, and reporting
"""

import json
import asyncio
from datetime import datetime
from typing import List, Dict

from config import DEFAULT_GEOS
from news_parser import NewsParser
from llm_processor import LLMProcessor
from report_generator import ReportGenerator
from notification_manager import NotificationManager


class MonitoringPipeline:
    def __init__(self):
        self.news_parser = NewsParser()
        self.llm_processor = LLMProcessor()
        self.report_generator = ReportGenerator()

    def run_for_geo(self, geo: str) -> Dict:
        """Run complete pipeline for a single GEO"""
        print(f"\n{'='*60}")
        print(f"🚀 PROCESSING GEO: {geo}")
        print(f"{'='*60}\n")

        # Step 1: Aggregate news
        print(f"📰 Step 1: Aggregating news...")
        news_items = self.news_parser.aggregate_news(geo)
        print(f"   ✅ Found {len(news_items)} news items")

        if not news_items:
            print(f"   ⚠️ No news found for {geo}")
            return None

        # Step 2: Classify news (Haiku - fast + cheap)
        print(f"🏷️  Step 2: Classifying news with Haiku...")
        classified_items = self.llm_processor.classify_news(news_items)
        print(f"   ✅ Classified {len(classified_items)} items")

        # Step 3: Generate angles (Sonnet - quality)
        print(f"💡 Step 3: Generating marketing angles with Sonnet...")
        angles = self.llm_processor.generate_angles(classified_items, geo)
        print(f"   ✅ Generated {len(angles)} angles")

        # Step 4: Generate headlines (Sonnet)
        print(f"📝 Step 4: Generating ad headlines with Sonnet...")
        headlines = self.llm_processor.generate_headlines(angles)
        print(f"   ✅ Generated {len(headlines)} headlines")

        # Step 5: Assess risks (Sonnet)
        print(f"⚠️  Step 5: Assessing risks with Sonnet...")
        risks = self.llm_processor.assess_risks(classified_items)
        print(f"   ✅ Assessed {len(risks)} items")

        # Step 6: Generate report
        print(f"📊 Step 6: Generating report...")
        report = self.report_generator.generate_report(
            geo=geo,
            news_items=classified_items,
            angles=angles,
            headlines=headlines,
            risks=risks,
            responsible_lead="AI Monitor",
        )
        print(f"   ✅ Report generated")

        # Step 7: Format and notify
        print(f"📢 Step 7: Sending notifications...")
        report_text = self.report_generator.format_report_text(report)
        notification_results = NotificationManager.send_report(report_text, report, geo)
        print(f"   ✅ Notifications sent: {notification_results}")

        return report

    def run_all_geos(self) -> List[Dict]:
        """Run pipeline for all configured GEOs"""
        print("\n" + "="*60)
        print("🌍 AI NEWS MONITORING PIPELINE")
        print(f"Processing GEOs: {', '.join(DEFAULT_GEOS)}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        all_reports = []

        for geo in DEFAULT_GEOS:
            try:
                report = self.run_for_geo(geo)
                if report:
                    all_reports.append(report)
            except Exception as e:
                print(f"❌ Error processing {geo}: {e}")
                import traceback
                traceback.print_exc()

        # Summary
        print("\n" + "="*60)
        print("✅ PIPELINE COMPLETE")
        print(f"Processed {len(all_reports)} GEOs")
        print(f"Total news items: {sum(r['stats']['total_news'] for r in all_reports)}")
        print(f"Total angles: {sum(r['stats']['total_angles'] for r in all_reports)}")
        print(f"Total headlines: {sum(r['stats']['total_headlines'] for r in all_reports)}")
        print("="*60 + "\n")

        return all_reports

    def save_reports(self, reports: List[Dict], output_dir: str = "."):
        """Save reports to JSON files"""
        for report in reports:
            geo = report["header"]["geo"]
            filename = f"{output_dir}/report_{geo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"💾 Saved report: {filename}")


def main():
    """Main entry point"""
    pipeline = MonitoringPipeline()

    # Run for all configured GEOs
    reports = pipeline.run_all_geos()

    # Save reports
    if reports:
        pipeline.save_reports(reports)

    return reports


if __name__ == "__main__":
    main()
