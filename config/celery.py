from celery import Celery
from celery.schedules import crontab

celery_app = Celery("DjangoCelery")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()


celery_app.conf.beat_schedule = {
    # Queue up the workflows every 5 minutes.
    # "progress-workflow-task": {
    #     "task": "core.tasks.progress_workflows",
    #     "schedule": crontab(minute="*/5"),
    # },
    # Nightly tasks to update the Staff search index.
    # "update-staff-search-index-from-activity-stream": {
    #     "task": "core.tasks.update_staff_search_index_from_activity_stream",
    #     "schedule": crontab(minute="0", hour="1"),
    # },
    # "update-staff-search-index-from-people-finder": {
    #     "task": "core.tasks.update_staff_search_index_from_people_finder",
    #     "schedule": crontab(minute="0", hour="2"),
    # },
    # "update-staff-search-index-from-service-now": {
    #     "task": "core.tasks.update_staff_search_index_from_service_now",
    #     "schedule": crontab(minute="0", hour="2"),
    # },
}
