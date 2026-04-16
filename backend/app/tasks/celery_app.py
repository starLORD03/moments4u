"""Re-export the celery app for CLI access: celery -A app.tasks.celery_app worker"""

from . import celery_app

__all__ = ["celery_app"]
