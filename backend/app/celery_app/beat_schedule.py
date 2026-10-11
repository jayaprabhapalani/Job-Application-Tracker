from celery.schedules import crontab

BEAT_SCHEDULE = {
    "check-stale-applications-daily": {
        "task": "app.celery_app.tasks.check_stale_applications",
        "schedule": crontab(hour=9, minute=0),
    },
    "cleanup-old-jobs-weekly": {
        "task": "app.celery_app.tasks.cleanup_old_jobs",
        "schedule": crontab(hour=0, minute=0, day_of_week=0),
    },
}
