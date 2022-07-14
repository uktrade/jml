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
    "asset_registry",
    "leavers",
    "user",
    "core",
    "core.cookies",
    "core.landing_pages",
    "core.health_check.apps.HealthCheckConfig",
    "core.staff_search",
    "activity_stream",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "health_check.contrib.migrations",
    "health_check.contrib.celery",
    "health_check.contrib.celery_ping",
    "health_check.contrib.redis",
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
    "core.middleware.XRobotsTagMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache_table",
    }
}

# Redis
REDIS_URL = os.environ.get("REDIS_URL")

# Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"

# Crispy forms
CRISPY_ALLOWED_TEMPLATE_PACKS = ["gds"]
CRISPY_TEMPLATE_PACK = "gds"

# Media /PS-IGNORE
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

# Dev tools & Authbroker
DEV_TOOLS_ENABLED = env.bool("DEV_TOOLS_ENABLED", default=False)

if DEV_TOOLS_ENABLED:
    INSTALLED_APPS += [
        "dev_tools.apps.DevToolsConfig",
    ]

    LOGIN_URL = reverse_lazy("dev_tools:index")
else:
    AUTHENTICATION_BACKENDS.append("user.backends.CustomAuthbrokerBackend")
    MIDDLEWARE.append("authbroker_client.middleware.ProtectAllViewsMiddleware")

# Slack
SLACK_API_TOKEN = env("SLACK_API_TOKEN", default=None)
SLACK_SRE_CHANNEL_ID = env("SLACK_SRE_CHANNEL_ID", default=None)

# Hawk
PEOPLE_FINDER_HAWK_ACCESS_ID = env("PEOPLE_FINDER_HAWK_ACCESS_ID")
PEOPLE_FINDER_HAWK_SECRET_KEY = env("PEOPLE_FINDER_HAWK_SECRET_KEY")

# People Finder
PEOPLE_FINDER_URL = env("PEOPLE_FINDER_URL")
PEOPLE_FINDER_INTERFACE = env("PEOPLE_FINDER_INTERFACE")

# People Data report
PEOPLE_DATA_INTERFACE = env("PEOPLE_DATA_INTERFACE")
if env("PEOPLE_DATA_ON", default="false") == "true":
    DATABASES["people_data"] = {
        "HOST": env("PEOPLE_DATA_POSTGRES_HOST"),
        "NAME": env("PEOPLE_DATA_POSTGRES_DATABASE"),
        "PORT": env("PEOPLE_DATA_POSTGRES_PORT", default=5432),
        "ENGINE": "django.db.backends.postgresql",
        "USER": env("PEOPLE_DATA_POSTGRES_USERNAME"),
        "PASSWORD": env("PEOPLE_DATA_POSTGRES_PASSWORD"),
    }

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
SERVICE_NOW_POST_LEAVER_REQUEST = env("SERVICE_NOW_POST_LEAVER_REQUEST", default=None)
SERVICE_NOW_GET_ASSET_PATH = env("SERVICE_NOW_GET_ASSET_PATH", default=None)
SERVICE_NOW_GET_USER_PATH = env("SERVICE_NOW_GET_USER_PATH", default=None)
SERVICE_NOW_GET_DIRECTORATE_PATH = env("SERVICE_NOW_GET_DIRECTORATE_PATH", default=None)
SERVICE_NOW_DIT_DEPARTMENT_SYS_ID = env(
    "SERVICE_NOW_DIT_DEPARTMENT_SYS_ID", default=None
)

# UK SBS API
UKSBS_INTERFACE = env("UKSBS_INTERFACE", default=None)
UKSBS_CLIENT_ID = env("UKSBS_CLIENT_ID", default=None)
UKSBS_CLIENT_SECRET = env("UKSBS_CLIENT_SECRET", default=None)
UKSBS_TOKEN_URL = env("UKSBS_TOKEN_URL", default=None)
UKSBS_HIERARCHY_API_URL = env("UKSBS_HIERARCHY_API_URL", default=None)
UKSBS_GET_PEOPLE_HIERARCHY = env("UKSBS_GET_PEOPLE_HIERARCHY", default=None)
UKSBS_LEAVER_API_URL = env("UKSBS_LEAVER_API_URL", default=None)
UKSBS_POST_LEAVER_SUBMISSION = env("UKSBS_POST_LEAVER_SUBMISSION", default=None)

# Legacy People Finder
LEGACY_PEOPLE_FINDER_ES_INDEX = env("LEGACY_PEOPLE_FINDER_ES_INDEX", default=None)
LEGACY_PEOPLE_FINDER_ES_URL = env("LEGACY_PEOPLE_FINDER_ES_URL", default=None)

# CSU4 Settings
CSU4_EMAIL = env("CSU4_EMAIL", default=None)

# OCS Settings
OCS_EMAIL = env("OCS_EMAIL", default=None)
OCS_OAB_LOCKER_EMAIL = env("OCS_OAB_LOCKER_EMAIL", default=None)

# Security Team Settings
SECURITY_TEAM_EMAIL = env("SECURITY_TEAM_EMAIL", default=None)

# SRE Team Settings
SRE_EMAIL = env("SRE_EMAIL", default=None)

# GOV.UK Notify
GOVUK_NOTIFY_API_KEY = env("GOVUK_NOTIFY_API_KEY", default=None)

# Email Templates
TEMPLATE_ID_LEAVER_THANK_YOU_EMAIL = env(
    "TEMPLATE_ID_LEAVER_THANK_YOU_EMAIL", default=None
)
TEMPLATE_ID_CSU4_EMAIL = env("TEMPLATE_ID_CSU4_EMAIL", default=None)
TEMPLATE_ID_OCS_LEAVER_EMAIL = env("TEMPLATE_ID_OCS_LEAVER_EMAIL", default=None)
TEMPLATE_ID_OCS_OAB_LOCKER_EMAIL = env("TEMPLATE_ID_OCS_OAB_LOCKER_EMAIL", default=None)
TEMPLATE_ID_ROSA_LEAVER_REMINDER_EMAIL = env(
    "TEMPLATE_ID_ROSA_LEAVER_REMINDER_EMAIL", default=None
)
TEMPLATE_ID_ROSA_LINE_MANAGER_REMINDER_EMAIL = env(
    "TEMPLATE_ID_ROSA_LINE_MANAGER_REMINDER_EMAIL", default=None
)
TEMPLATE_ID_SECURITY_TEAM_OFFBOARD_LEAVER_EMAIL = env(
    "TEMPLATE_ID_SECURITY_TEAM_OFFBOARD_LEAVER_EMAIL", default=None
)
TEMPLATE_ID_SECURITY_TEAM_OFFBOARD_LEAVER_REMINDER_EMAIL = env(
    "TEMPLATE_ID_SECURITY_TEAM_OFFBOARD_LEAVER_REMINDER_EMAIL", default=None
)
TEMPLATE_ID_SRE_REMINDER_EMAIL = env("TEMPLATE_ID_SRE_REMINDER_EMAIL", default=None)
TEMPLATE_ID_LINE_MANAGER_CORRECTION_EMAIL = env(
    "TEMPLATE_ID_LINE_MANAGER_CORRECTION_EMAIL", default=None
)
TEMPLATE_ID_LINE_MANAGER_NOTIFICATION_EMAIL = env(
    "TEMPLATE_ID_LINE_MANAGER_NOTIFICATION_EMAIL", default=None
)
TEMPLATE_ID_LINE_MANAGER_REMINDER_EMAIL = env(
    "TEMPLATE_ID_LINE_MANAGER_REMINDER_EMAIL", default=None
)
TEMPLATE_ID_LINE_MANAGER_THANKYOU_EMAIL = env(
    "TEMPLATE_ID_LINE_MANAGER_THANKYOU_EMAIL", default=None
)

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

# Index Current user middleware
if env("INDEX_CURRENT_USER_MIDDLEWARE", default="false") == "true":
    MIDDLEWARE.append("core.middleware.IndexCurrentUser")

# DIT Activity Stream settings
DIT_ACTIVITY_STREAM_CLIENT_CLASS = "leavers.client.ActivityStreamUserClient"
DJANGO_HAWK = {
    "HAWK_INCOMING_ACCESS_KEY": env("HAWK_INCOMING_ACCESS_KEY"),
    "HAWK_INCOMING_SECRET_KEY": env("HAWK_INCOMING_SECRET_KEY"),
}

# Process leaving requests
PROCESS_LEAVING_REQUEST = env.bool("PROCESS_LEAVING_REQUEST", default=True)

JML_TEAM_CONTACT_EMAIL = env("JML_TEAM_CONTACT_EMAIL", default="")
