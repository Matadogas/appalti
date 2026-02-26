"""Celery app configuration."""
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "tristate_bids",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/New_York",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Schedule daily scrapes at 6 AM EST
celery_app.conf.beat_schedule = {
    "run-daily-scrapes": {
        "task": "app.worker.tasks.run_all_scrapers",
        "schedule": crontab(hour=6, minute=0),
    },
}
