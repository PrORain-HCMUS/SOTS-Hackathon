"""
Celery application configuration.
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "agripulse",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks_discover",
        "app.workers.tasks_preprocess",
        "app.workers.tasks_infer",
        "app.workers.tasks_aggregate",
        "app.workers.tasks_alerts",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Celery Beat schedule - runs every 6 hours
celery_app.conf.beat_schedule = {
    "discover-scenes-every-6-hours": {
        "task": "app.workers.tasks_discover.discover_new_scenes",
        "schedule": crontab(minute=0, hour="*/6"),
        "args": (),
    },
}
