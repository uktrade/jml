#!/bin/bash -e
if [ -n "${COPILOT_ENVIRONMENT_NAME}" ]; then
  echo "Running in DBT Platform"
else
  echo "Running in GOV PaaS"
  npm run build
  python manage.py collectstatic --no-input
fi
python manage.py migrate --noinput
waitress-serve --port=$PORT config.wsgi:application
