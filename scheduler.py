#!/usr/bin/env python3
"""
Scheduler for automated pipeline runs
Options: APScheduler, cron, Windows Task Scheduler
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import logging
from main import MonitoringPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.pipeline = MonitoringPipeline()

    def run_pipeline_job(self):
        """Job to run the monitoring pipeline"""
        logger.info(f"🚀 Starting scheduled pipeline run at {datetime.now()}")
        try:
            reports = self.pipeline.run_all_geos()
            self.pipeline.save_reports(reports)
            logger.info(f"✅ Pipeline completed successfully at {datetime.now()}")
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            import traceback
            traceback.print_exc()

    def schedule_every_3_days(self):
        """Schedule pipeline to run every 3 days at 9 AM"""
        self.scheduler.add_job(
            self.run_pipeline_job,
            'interval',
            days=3,
            id='news_monitoring_3days',
            name='News Monitoring Pipeline (Every 3 days)',
            replace_existing=True,
        )
        logger.info("📅 Scheduled: Pipeline runs every 3 days")

    def schedule_every_6_hours(self):
        """Schedule pipeline to run every 6 hours (for testing)"""
        self.scheduler.add_job(
            self.run_pipeline_job,
            'interval',
            hours=6,
            id='news_monitoring_6h',
            name='News Monitoring Pipeline (Every 6 hours)',
            replace_existing=True,
        )
        logger.info("📅 Scheduled: Pipeline runs every 6 hours")

    def schedule_cron(self, cron_expression: str):
        """
        Schedule with cron expression
        Examples:
        - "0 9 * * 1,4" = 9 AM Monday and Thursday
        - "0 9 * * *" = 9 AM every day
        - "0 */6 * * *" = Every 6 hours
        """
        from apscheduler.triggers.cron import CronTrigger

        trigger = CronTrigger.from_crontab(cron_expression)
        self.scheduler.add_job(
            self.run_pipeline_job,
            trigger=trigger,
            id='news_monitoring_cron',
            name=f'News Monitoring Pipeline ({cron_expression})',
            replace_existing=True,
        )
        logger.info(f"📅 Scheduled with cron: {cron_expression}")

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Scheduler started")
            # Keep scheduler running
            try:
                while True:
                    pass
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("⏹️ Scheduler stopped")

    def list_jobs(self):
        """List all scheduled jobs"""
        jobs = self.scheduler.get_jobs()
        logger.info(f"📋 Scheduled jobs ({len(jobs)}):")
        for job in jobs:
            logger.info(f"  - {job.name} | Next run: {job.next_run_time}")


# ============================================================================
# CRON SETUP EXAMPLES
# ============================================================================

CRON_EXAMPLES = {
    "daily_9am": "0 9 * * *",  # Every day at 9 AM
    "every_3_days": "0 9 */3 * *",  # Every 3 days at 9 AM
    "twice_weekly": "0 9 * * 1,4",  # Monday and Thursday at 9 AM
    "hourly": "0 * * * *",  # Every hour
    "every_6_hours": "0 */6 * * *",  # Every 6 hours
    "midnight": "0 0 * * *",  # Every day at midnight
}

# ============================================================================
# WINDOWS TASK SCHEDULER
# ============================================================================

WINDOWS_BATCH_TEMPLATE = r"""
@echo off
REM Windows Task Scheduler - Run news monitoring pipeline

REM Set working directory
cd /d "C:\Users\kokok\Desktop\Test"

REM Set UTF-8 encoding for console output
set PYTHONIOENCODING=utf-8

REM Run the pipeline
python main.py

REM Log the result
echo Pipeline completed at %date% %time% >> pipeline.log
"""

# ============================================================================
# LINUX/MAC CRONTAB
# ============================================================================

UNIX_CRONTAB_TEMPLATE = """
# Edit crontab with: crontab -e
# Run every 3 days at 9 AM
0 9 */3 * * cd /path/to/project && python main.py >> /var/log/news_monitoring.log 2>&1

# Or with systemd timer (recommended)
# Create /etc/systemd/system/news-monitoring.service
# Create /etc/systemd/system/news-monitoring.timer
# Then: sudo systemctl enable news-monitoring.timer
"""


def main():
    """Main entry point for scheduler"""
    scheduler = PipelineScheduler()

    # Choose one schedule:
    # scheduler.schedule_every_3_days()
    # scheduler.schedule_every_6_hours()
    scheduler.schedule_cron(CRON_EXAMPLES["twice_weekly"])  # Monday & Thursday

    # List jobs
    scheduler.list_jobs()

    # Start scheduler
    logger.info("\n🚀 Starting scheduler. Press Ctrl+C to stop.\n")
    scheduler.start()


if __name__ == "__main__":
    main()
