# https://stackabuse.com/asynchronous-tasks-in-django-with-redis-and-celery/
import os
from celery import Celery

celery_app = Celery("DjangoCelery")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()


@celery_app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
