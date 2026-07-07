from __future__ import annotations

from loguru import logger
from app.config import settings

# Celery è opzionale — se Redis non è disponibile, usa broker in memoria
_celery_available = False
_celery_redis_available = False

try:
    # Verifica se Redis è raggiungibile
    from redis import Redis
    r = Redis.from_url(settings.celery_broker_url)
    r.ping()
    r.close()
    _celery_redis_available = True
except Exception:
    logger.warning("Redis non disponibile, Celery userà broker in memoria")
    _celery_redis_available = False

broker_url = settings.celery_broker_url if _celery_redis_available else "memory://"
backend_url = settings.celery_result_backend if _celery_redis_available else "memory://"

try:
    from celery import Celery

    celery_app = Celery(
        "video_ai",
        broker=broker_url,
        backend=backend_url,
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
    )
    _celery_available = True
    logger.info(f"Celery configurato (broker={'redis' if _celery_redis_available else 'memory'})")
except Exception as e:
    logger.warning(f"Celery non disponibile: {e}")
    celery_app = None
    _celery_available = False


def run_worker():
    if celery_app:
        celery_app.worker_main(argv=["worker", "--loglevel=info", "--concurrency=2"])
    else:
        logger.error("Celery non disponibile, impossibile avviare worker")
