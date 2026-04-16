"""
Celery application configuration.

Sets up the Celery instance with Redis as broker and
configures the beat schedule for periodic tasks.
"""

from celery import Celery
from celery.schedules import crontab

from ..config import get_settings

settings = get_settings()

celery_app = Celery(
    "moments4u",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.face_processing",
        "app.tasks.cleanup",
        "app.tasks.thumbnail",
    ],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Reliability
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Results
    result_expires=3600,  # 1 hour
    # Beat schedule (periodic tasks)
    beat_schedule={
        "cleanup-expired-photos": {
            "task": "app.tasks.cleanup.cleanup_expired_photos",
            "schedule": crontab(hour=settings.cleanup_cron_hour, minute=0),
        },
    },
)
