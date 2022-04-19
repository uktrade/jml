from celery import Celery
from celery.schedules import crontab

celery_app = Celery("DjangoCelery")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()


celery_app.conf.beat_schedule = {
    # Queue up the workflows every 5 minutes.
    "progress-workflow-task": {
        "task": "core.tasks.progress_workflows",
        "schedule": crontab(minute="*/5"),
    }
}
