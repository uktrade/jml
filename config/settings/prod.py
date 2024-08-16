import os
import sys
from urllib.parse import urlparse

import sentry_sdk
from dbt_copilot_python.utility import is_copilot
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # type: ignore # noqa

# SSO requirement
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# X_ROBOTS_TAG (https://man.uktrade.io/docs/procedures/1st-go-live.html)
X_ROBOTS_TAG = [
    "noindex",
    "nofollow",
]

# Sentry
sentry_environment = os.environ.get("SENTRY_ENVIRONMENT")
if is_copilot():
    sentry_environment = f"aws-{sentry_environment}"


def filter_transactions(event, hint):
    url_string = event["request"]["url"]
    parsed_url = urlparse(url_string)

    if parsed_url.path.startswith(("/pingdom", "/healthcheck")):
        return None

    return event


sentry_sdk.init(
    os.environ.get("SENTRY_DSN"),
    environment=sentry_environment,
    integrations=[DjangoIntegration()],
    enable_tracing=os.environ.get("SENTRY_ENABLE_TRACING", "false").lower() == "true",
    traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
    before_send_transaction=filter_transactions,
)

# Django staff SSO user migration process requries the following
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

# Set anti XSS header
SECURE_BROWSER_XSS_FILTER = True

# Audit log middleware user field
AUDIT_LOG_USER_FIELD = "username"
