#!/bin/bash -e
if [ -n "${COPILOT_ENVIRONMENT_NAME}" ]; then
  echo "Running in DBT Platform"
  npm run build
  python manage.py migrate --noinput
else
  echo "Running in GOV PaaS"
  if [ "$INSTANCE_INDEX" == 0 ]; then
    npm run build
    python manage.py collectstatic --no-input
    python manage.py migrate --noinput
  fi
fi

waitress-serve --port=$PORT config.wsgi:application
