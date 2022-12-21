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
    },
    # Search for uncomplete leavers once a day.
    # Execute daily at 7am
    "uncomplete-leaverpay-cut-off-task": {
        "task": "leavers.tasks.notify_hr",
        "schedule": crontab(minute=0, hour=7, day_of_week='mon,tue,wed,thu,fri'),
    },
    # Nightly tasks to update the Staff search index.
    "ingest-activity-stream-task": {
        "task": "core.tasks.ingest_activity_stream_task",
        "schedule": crontab(minute="0", hour="3"),
    },
    "index-sso-users-task": {
        "task": "core.tasks.index_sso_users_task",
        "schedule": crontab(minute="0", hour="4"),
    },
    "ingest-people-data-task": {
        "task": "core.tasks.ingest_people_data_task",
        "schedule": crontab(minute="0", hour="5"),
    },
    "ingest-people-finder-task": {
        "task": "core.tasks.ingest_people_finder_task",
        "schedule": crontab(minute="0", hour="5"),
    },
    "ingest-service-now-task": {
        "task": "core.tasks.ingest_service_now_task",
        "schedule": crontab(minute="0", hour="5"),
    },
}
