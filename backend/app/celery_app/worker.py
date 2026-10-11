from celery import Celery
from app.config import settings
from app.celery_app.beat_schedule import BEAT_SCHEDULE

celery_app = Celery(
    "job_tracker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.celery_app.tasks"],
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    beat_schedule=BEAT_SCHEDULE,
)
