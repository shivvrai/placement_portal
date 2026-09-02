"""
Celery worker configuration.
"""

from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ccip",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.adapters.ums_tasks",  # UMS sync tasks
        # "app.nlp.tasks",
        # "app.ml.tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,   # 10 minute hard limit per task
    task_soft_time_limit=540,  # 9 minute soft limit
    worker_max_tasks_per_child=100,  # restart worker after 100 tasks (prevent memory leaks)
    # ── Celery Beat schedule (run: celery -A app.worker beat) ──────────────
    beat_schedule={
        "nightly-ums-sync": {
            "task": "ums.scheduled_full_sync",
            "schedule": crontab(hour=2, minute=0),  # every night at 2:00 AM UTC
            "options": {"queue": "ums"},
        },
    },
    task_routes={
        "ums.*": {"queue": "ums"},
    },
)
