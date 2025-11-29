from celery import Celery

import app.worker.tasks  # noqa: F401
from app.core.config import settings

# Брокер и бэкенд — Redis
CELERY_BROKER_URL = settings.redis_url
CELERY_RESULT_BACKEND = settings.redis_url

celery_app = Celery(
    "movie_recommender",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


celery_app.autodiscover_tasks(
    packages=["app.worker"],
)
