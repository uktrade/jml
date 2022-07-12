web: python manage.py compilescss && python manage.py collectstatic && python manage.py migrate && waitress-serve --port=$PORT config.wsgi:application
beat: celery -A config.celery beat -l INFO
worker: celery -A config.celery worker -l INFO
