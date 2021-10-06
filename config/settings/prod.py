import sys

from .base import *  # noqa
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from django_log_formatter_ecs import ECSFormatter


# X_ROBOTS_TAG (https://man.uktrade.io/docs/procedures/1st-go-live.html)
X_ROBOTS_TAG = [
    'noindex',
    'nofollow',
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "ecs_formatter": {
            "()": ECSFormatter,
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'ecs': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'ecs_formatter',
        },
        'stdout': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'simple',
            'level': 'INFO',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['ecs', ],
            'level': 'INFO',
            'propagate': True,
        },
        'forecast.import_csv': {
            'handlers': ['stdout', ],
            'level': 'INFO',
            'propagate': True,
        },
        'forecast.views.upload_file': {
            'handlers': ['stdout', ],
            'level': 'INFO',
            'propagate': True,
        },
        'forecast.tasks': {
            'handlers': ['stdout', ],
            'level': 'INFO',
            'propagate': True,
        }
    },
}

# Set async file uploading
ASYNC_FILE_UPLOAD = True

sentry_sdk.init(
    os.environ.get("SENTRY_DSN"),
    environment=os.environ.get("SENTRY_ENVIRONMENT"),
    integrations=[DjangoIntegration()],
)

# Django staff SSO user migration process requries the following
MIGRATE_EMAIL_USER_ON_LOGIN = True

# HSTS (https://man.uktrade.io/docs/procedures/1st-go-live.html)
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# ## IHTC compliance

# Set crsf cookie to be secure
CSRF_COOKIE_SECURE = True

# Set session cookie to be secure
SESSION_COOKIE_SECURE = True

# Make browser end session when user closes browser
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Set cookie expiry to 4 hours
SESSION_COOKIE_AGE = 4 * 60 * 60  # 4 hours in seconds

# Prevent client side JS from accessing CRSF token
CSRF_COOKIE_HTTPONLY = True

# Prevent client side JS from accessing session cookie (true by default)
SESSION_COOKIE_HTTPONLY = True

# Set content to no sniff
SECURE_CONTENT_TYPE_NOSNIFF = True

# Set anti XSS header
SECURE_BROWSER_XSS_FILTER = True

# Audit log middleware user field
AUDIT_LOG_USER_FIELD = "username"
