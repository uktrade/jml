web: python manage.py compilescss && python manage.py collectstatic && python manage.py migrate && waitress-serve --port=$PORT config.wsgi:application
celery-beat: celery -A config beat -l INFO