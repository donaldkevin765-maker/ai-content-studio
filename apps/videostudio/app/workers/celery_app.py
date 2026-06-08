from __future__ import annotations

from celery import Celery
from app.config import settings

celery_app = Celery(
    "video_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Rome",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=600,
    task_time_limit=900,
    beat_schedule={
        "cleanup-old-outputs": {
            "task": "app.workers.tasks.cleanup_old_outputs",
            "schedule": 86400.0,
        },
    },
)


def run_worker():
    celery_app.worker_main(argv=["worker", "--loglevel=info", "--concurrency=2"])
