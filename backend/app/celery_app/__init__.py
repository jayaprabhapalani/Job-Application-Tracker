from celery import Celery
import os

# Set default Django settings module
os.environ.setdefault('CELERY_CONFIG_MODULE', 'app.celery_app')

# Create Celery app
celery_app = Celery('job_tracker')

# Load configuration from config module
celery_app.config_from_object('app.config', namespace='CELERY')

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.celery_app.tasks'])

# Beat schedule
celery_app.conf.beat_schedule = {}
