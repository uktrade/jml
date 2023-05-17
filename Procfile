web: npm run build && python manage.py collectstatic && waitress-serve --port=$PORT config.wsgi:application
beat: celery -A config.celery beat -l INFO
worker: celery -A config.celery worker -l INFO
