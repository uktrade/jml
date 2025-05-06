from celery import Celery
from celery.schedules import crontab
from dbt_copilot_python.celery_health_check import healthcheck

celery_app = Celery("DjangoCelery")
celery_app = healthcheck.setup(celery_app)
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()

celery_app.conf.beat_schedule = {
    # Queue up the workflows every 5 minutes.
    "progress-workflow-task": {
        "task": "core.tasks.progress_workflows",
        "schedule": crontab(minute="*/5"),
    },
    # Ingest Data from S3 every 30mins
    # TODO: UNCOMMENT BELOW TASK AFTER PEN TEST
    # "ingest-activity-stream-task": {
    #     "task": "core.tasks.ingest_activity_stream_task",
    #     "schedule": crontab(minute="*/30"),
    # },
    # TODO: UNCOMMENT BELOW TASK AFTER PEN TEST
    # "ingest-people-s3-task": {
    #     "task": "core.tasks.ingest_people_s3_task",
    #     "schedule": crontab(minute="*/30"),
    # },
    # Search for incomplete leavers once a day.
    # Execute daily at 7am
    "incomplete-leaver-pay-cut-off-task": {
        "task": "leavers.tasks.notify_hr",
        "schedule": crontab(minute=0, hour=7, day_of_week="mon,tue,wed,thu,fri"),
    },
    # Send weekly email to notify of last week's leavers.
    # Execute on monday morning at 8 am
    "weekly-leavers-email-task": {
        "task": "leavers.tasks.weekly_leavers_email",
        "schedule": crontab(minute=0, hour=8, day_of_week="mon"),
    },
    # Nightly tasks to update the Staff search index.
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
