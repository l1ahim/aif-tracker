from celery import Celery
from celery.schedules import crontab
import os

from app.core.config import settings

# Initialize Celery
celery_app = Celery(
    "aif_tracker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.background_tasks"]
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    "generate-monthly-insights": {
        "task": "app.tasks.background_tasks.generate_monthly_insights_for_all_users",
        "schedule": crontab(day_of_month=1, hour=0, minute=0),  # First day of each month
    },
    "check-budget-alerts": {
        "task": "app.tasks.background_tasks.check_budget_alerts_for_all_users",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
    },
    "cleanup-old-receipts": {
        "task": "app.tasks.background_tasks.cleanup_old_receipts",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}

if __name__ == "__main__":
    celery_app.start()
