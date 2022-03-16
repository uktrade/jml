import os
from pathlib import Path
from typing import List

import environ
from django.urls import reverse_lazy
from django_log_formatter_ecs import ECSFormatter

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
env.read_env()

APP_ENV = env("APP_ENV")

DEBUG = env.bool("DEBUG", default=False)

SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

VCAP_SERVICES = env.json("VCAP_SERVICES", {})

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "sass_processor",
    "django_workflow_engine",
    "django_celery_beat",
    "django_celery_results",
    "crispy_forms",
    "crispy_forms_gds",
    "notifications_python_client",
    "authbroker_client",
    "rest_framework",
    "leavers",
    "user",
    "core",
    "core.cookies",
    "core.staff_search",
    "api",
    "activity_stream",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "dev_tools.views.dev_tools_context",
                "core.context_processors.global_context",
            ]
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

VCAP_SERVICES = env.json("VCAP_SERVICES", default={})

if "postgres" in VCAP_SERVICES:
    DATABASE_URL = VCAP_SERVICES["postgres"][0]["credentials"]["uri"]
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

DATABASES = {"default": env.db()}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "ecs_formatter": {
            "()": ECSFormatter,
        },
        "simple": {
            "format": "{asctime} {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "ecs": {
            "class": "logging.StreamHandler",
            "formatter": "ecs_formatter",
        },
        "simple": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": [
            "ecs",
            "simple",
        ],
        "level": os.getenv("ROOT_LOG_LEVEL", "INFO"),  # noqa F405
    },
    "loggers": {
        "django": {
            "handlers": [
                "ecs",
                "simple",
            ],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),  # noqa F405
            "propagate": False,
        },
        "django.server": {
            "handlers": [
                "ecs",
                "simple",
            ],
            "level": os.getenv("DJANGO_SERVER_LOG_LEVEL", "ERROR"),  # noqa F405
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": [
                "ecs",
                "simple",
            ],
            "level": os.getenv("DJANGO_DB_LOG_LEVEL", "ERROR"),  # noqa F405
            "propagate": False,
        },
    },
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },  # noqa
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/
LANGUAGE_CODE = "en-gb"  # must be gb for date entry to work
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

AUTH_USER_MODEL = "user.User"

# SSO
AUTHBROKER_URL = env("AUTHBROKER_URL", default=None)
AUTHBROKER_CLIENT_ID = env("AUTHBROKER_CLIENT_ID", default=None)
AUTHBROKER_CLIENT_SECRET = env("AUTHBROKER_CLIENT_SECRET", default=None)
AUTHBROKER_SCOPES = "read write"

LOGIN_URL = "/auth/login"
LOGIN_REDIRECT_URL = "/"  # "leavers:leavers_form"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"

CAN_ELEVATE_SSO_USER_PERMISSIONS = False
CAN_CREATE_TEST_USER = False

STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "sass_processor.finders.CssFinder",
]

STATICFILES_DIRS = [
    BASE_DIR / "assets/",
    BASE_DIR / "node_modules/",
]

SASS_PROCESSOR_INCLUDE_DIRS = [
    str(BASE_DIR / "node_modules"),
]

GTM_CODE = env("GTM_CODE", default=None)

SETTINGS_EXPORT = [
    "DEBUG",
    "GTM_CODE",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "authbroker_client.middleware.ProtectAllViewsMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "user.backends.CustomAuthbrokerBackend",
]

DEV_TOOLS_ENABLED = APP_ENV in ("local", "dev")

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache_table",
    }
}

# Crispy forms
CRISPY_ALLOWED_TEMPLATE_PACKS = ["gds"]
CRISPY_TEMPLATE_PACK = "gds"

# Media /PS-IGNORE
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

SLACK_API_TOKEN = env("SLACK_API_TOKEN", default=None)
SLACK_SRE_CHANNEL_ID = env("SLACK_SRE_CHANNEL_ID", default=None)

# Hawk
PEOPLE_FINDER_HAWK_ACCESS_ID = env("PEOPLE_FINDER_HAWK_ACCESS_ID")
PEOPLE_FINDER_HAWK_SECRET_KEY = env("PEOPLE_FINDER_HAWK_SECRET_KEY")

# People Finder
PEOPLE_FINDER_URL = env("PEOPLE_FINDER_URL")
PEOPLE_FINDER_INTERFACE = env("PEOPLE_FINDER_INTERFACE")

# Staff SSO
STAFF_SSO_ACTIVITY_STREAM_URL = env("STAFF_SSO_ACTIVITY_STREAM_URL", default=None)
STAFF_SSO_ACTIVITY_STREAM_ID = env("STAFF_SSO_ACTIVITY_STREAM_ID", default=None)
STAFF_SSO_ACTIVITY_STREAM_SECRET = env("STAFF_SSO_ACTIVITY_STREAM_SECRET", default=None)

# django-workflow-engine
DJANGO_WORKFLOWS = {
    "leaving": "leavers.workflow.leaving.LeaversWorkflow",
}

# Site's own URL
SITE_URL = env("SITE_URL")

# Service Now
SERVICE_NOW_INTERFACE = env("SERVICE_NOW_INTERFACE", default=None)
SERVICE_NOW_API_URL = env("SERVICE_NOW_API_URL", default=None)
SERVICE_NOW_POST_LEAVER_REQUEST = env("SERVICE_NOW_POST_LEAVER_REQUEST")
SERVICE_NOW_GET_ASSET_PATH = env("SERVICE_NOW_GET_ASSET_PATH")
SERVICE_NOW_GET_USER_PATH = env("SERVICE_NOW_GET_USER_PATH")
SERVICE_NOW_GET_DIRECTORATE_PATH = env("SERVICE_NOW_GET_DIRECTORATE_PATH")
SERVICE_NOW_DIT_DEPARTMENT_SYS_ID = env("SERVICE_NOW_DIT_DEPARTMENT_SYS_ID")

# Legacy People Finder
LEGACY_PEOPLE_FINDER_ES_INDEX = env("LEGACY_PEOPLE_FINDER_ES_INDEX", default=None)
LEGACY_PEOPLE_FINDER_ES_URL = env("LEGACY_PEOPLE_FINDER_ES_URL", default=None)

# GOV.UK Notify
GOVUK_NOTIFY_API_KEY = env("GOVUK_NOTIFY_API_KEY")

# CSU4 Settings
CSU4_EMAIL = env("CSU4_EMAIL")

# OCS Settings
OCS_EMAIL = env("OCS_EMAIL")

# Security Team Settings
SECURITY_TEAM_EMAIL = env("SECURITY_TEAM_EMAIL")

# SRE Team Settings
SRE_EMAIL = env("SRE_EMAIL")

# Email Templates
CSU4_EMAIL_TEMPLATE_ID = env("CSU4_EMAIL_TEMPLATE_ID", default=None)
OCS_LEAVER_EMAIL_TEMPLATE_ID = env("OCS_LEAVER_EMAIL_TEMPLATE_ID", default=None)
ROSA_LEAVER_REMINDER_EMAIL = env("ROSA_LEAVER_REMINDER_EMAIL", default=None)
ROSA_LINE_MANAGER_REMINDER_EMAIL = env("ROSA_LINE_MANAGER_REMINDER_EMAIL", default=None)
SECURITY_TEAM_OFFBOARD_LEAVER_EMAIL = env(
    "SECURITY_TEAM_OFFBOARD_LEAVER_EMAIL", default=None
)
SECURITY_TEAM_OFFBOARD_LEAVER_REMINDER_EMAIL = env(
    "SECURITY_TEAM_OFFBOARD_LEAVER_REMINDER_EMAIL", default=None
)
LINE_MANAGER_NOTIFICATION_EMAIL = env("LINE_MANAGER_NOTIFICATION_EMAIL", default=None)
LINE_MANAGER_REMINDER_EMAIL = env("LINE_MANAGER_REMINDER_EMAIL", default=None)
LINE_MANAGER_THANKYOU_EMAIL = env("LINE_MANAGER_THANKYOU_EMAIL", default=None)

# LSD Team settings
LSD_ZENDESK_EMAIL = env("LSD_ZENDESK_EMAIL")
LSD_ZENDESK_TOKEN = env("LSD_ZENDESK_TOKEN")
LSD_ZENDESK_SUBDOMAIN = env("LSD_ZENDESK_SUBDOMAIN")

# Search Staff Index
SEARCH_HOST_URLS: List[str] = []
if "opensearch" in VCAP_SERVICES:
    SEARCH_HOST_URLS = [VCAP_SERVICES["opensearch"][0]["credentials"]["uri"]]
else:
    SEARCH_HOST_URLS = env(
        "SEARCH_HOST_URLS",
        default="",
    ).split(",")

SEARCH_STAFF_INDEX_NAME = env("SEARCH_STAFF_INDEX_NAME", default="staff")
