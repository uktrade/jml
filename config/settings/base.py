import os
from pathlib import Path
from typing import List

import dj_database_url
import environ
from dbt_copilot_python.database import database_url_from_env
from dbt_copilot_python.network import setup_allowed_hosts
from dbt_copilot_python.utility import is_copilot
from django.urls import reverse_lazy
from django_log_formatter_asim import ASIMFormatter
from django_log_formatter_ecs import ECSFormatter

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
env.read_env()

APP_ENV = env("APP_ENV")

DEBUG = env.bool("DEBUG", default=False)

SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = setup_allowed_hosts(env.list("ALLOWED_HOSTS"))

VCAP_SERVICES = env.json("VCAP_SERVICES", {})

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_workflow_engine",
    "django_celery_beat",
    "django_celery_results",
    "crispy_forms",
    "crispy_forms_gds",
    "notifications_python_client",
    "authbroker_client",
    "rest_framework",
    "govuk_frontend_django",
    "asset_registry",
    "leavers",
    "user",
    "core",
    "core.accessibility",
    "core.cookies",
    "core.feedback",
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
        "DIRS": [BASE_DIR / "templates"],
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

if is_copilot():
    DATABASES = {
        "default": dj_database_url.config(
            default=database_url_from_env("DATABASE_CREDENTIALS")
        )
    }
else:
    if "postgres" in VCAP_SERVICES:
        DATABASE_URL = VCAP_SERVICES["postgres"][0]["credentials"]["uri"]
    else:
        DATABASE_URL = env("DATABASE_URL")

    DATABASES = {"default": env.db()}

DATABASE_ROUTERS = ["core.people_data.routers.PeopleDataRouter"]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "ecs_formatter": {
            "()": ECSFormatter,
        },
        "simple": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
        "asim_formatter": {
            "()": ASIMFormatter,
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
            "propagate": True,
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

if is_copilot():
    LOGGING["handlers"]["ecs"]["formatter"] = "asim_formatter"  # type: ignore[index]

DLFA_INCLUDE_RAW_LOG = True

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
AUTHBROKER_ANONYMOUS_URL_NAMES = (
    "leaving-requests-list",
    "leaving-requests-detail",
    "dit_activity_stream",
)

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
]

STATICFILES_DIRS = [
    BASE_DIR / "static/",
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
    "core.middleware.PrimaryEmailMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"


# Redis
if is_copilot():
    REDIS_URL = env("REDIS_URL", default=None) + "?ssl_cert_reqs=required"
elif "redis" in VCAP_SERVICES:
    credentials = VCAP_SERVICES["redis"][0]["credentials"]
    REDIS_URL = "rediss://:{}@{}:{}/0?ssl_cert_reqs=required".format(
        credentials["password"],
        credentials["host"],
        credentials["port"],
    )
else:
    REDIS_URL = env("REDIS_URL", default=None)


# Cache
# https://docs.djangoproject.com/en/4.0/topics/cache/
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": "cache",
    }
}


# Session
# https://docs.djangoproject.com/en/4.0/topics/http/sessions/
SESSION_ENGINE = "django.contrib.sessions.backends.cache"


# Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"

# Crispy forms
CRISPY_ALLOWED_TEMPLATE_PACKS = ["gds"]
CRISPY_TEMPLATE_PACK = "gds"

# Media /PS-IGNORE
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"


# Django REST Framework (DRF)

# Pagination
# https://www.django-rest-framework.org/api-guide/pagination/
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.CursorPagination",
    "PAGE_SIZE": 100,
}


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

DEPARTMENT_NAME = "Department for Business and Trade"
DEPARTMENT_ACRONYM = "DBT"
SERVICE_NAME = f"Leaving {DEPARTMENT_ACRONYM} service"

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
RUN_DJANGO_WORKFLOWS = env.bool("RUN_DJANGO_WORKFLOWS", default=False)


# Site's own URL
SITE_URL = env("SITE_URL")

# Service Now
SERVICE_NOW_ENABLE_ONLINE_PROCESS = env.bool(
    "SERVICE_NOW_ENABLE_ONLINE_PROCESS",
    default=False,
)
SERVICE_NOW_OFFLINE_URL = env("SERVICE_NOW_OFFLINE_URL", default=None)
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

# CLU4 Settings
CLU4_EMAIL = env("CLU4_EMAIL", default=None)

# Feetham Security Pass Office Settings
FEETHAM_SECURITY_PASS_OFFICE_EMAIL = env(
    "FEETHAM_SECURITY_PASS_OFFICE_EMAIL", default=None
)

# IT OPS Settings
IT_OPS_EMAIL = env("IT_OPS_EMAIL", default=None)

# OCS Settings
OCS_EMAIL = env("OCS_EMAIL", default=None)
OCS_OAB_LOCKER_EMAIL = env("OCS_OAB_LOCKER_EMAIL", default=None)

# Security Team Settings
SECURITY_TEAM_VETTING_EMAIL = env("SECURITY_TEAM_VETTING_EMAIL", default=None)
SECURITY_TEAM_BUILDING_PASS_EMAIL = env(
    "SECURITY_TEAM_BUILDING_PASS_EMAIL", default=None
)
SECURITY_TEAM_ROSA_EMAIL = env("SECURITY_TEAM_ROSA_EMAIL", default=None)

# SRE Team Settings
SRE_EMAIL = env("SRE_EMAIL", default=None)

# HR Team Settings
HR_UKSBS_CORRECTION_EMAIL = env("HR_UKSBS_CORRECTION_EMAIL", default=None)

# Health and Safety Team Settings
HEALTH_AND_SAFETY_EMAIL = env("HEALTH_AND_SAFETY_EMAIL", default="")

# COMAEA Team Settings
COMAEA_EMAIL = env("COMAEA_EMAIL", default=None)

# Business Continuity Team Settings
BUSINESS_CONTINUITY_EMAIL = env("BUSINESS_CONTINUITY_EMAIL", default=None)

# Workforce planning Team Settings
WORKFORCE_PLANNING_EMAIL = env("WORKFORCE_PLANNING_EMAIL", default=None)

# GOV.UK Notify
GOVUK_NOTIFY_API_KEY = env("GOVUK_NOTIFY_API_KEY", default=None)

# Search Staff Index
SEARCH_HOST_URLS: List[str] = []
if "opensearch" in VCAP_SERVICES:
    SEARCH_HOST_URLS = [VCAP_SERVICES["opensearch"][0]["credentials"]["uri"]]
else:
    SEARCH_HOST_URLS = env(
        "SEARCH_HOST_URLS",
        default=None,
    ).split(",")

SEARCH_STAFF_INDEX_NAME = env("SEARCH_STAFF_INDEX_NAME", default="staff")

# Index Current user middleware
if env("INDEX_CURRENT_USER_MIDDLEWARE", default="false") == "true":
    MIDDLEWARE.append("core.middleware.IndexCurrentUser")

# Django HAWK settings
DJANGO_HAWK = {
    "HAWK_INCOMING_ACCESS_KEY": env("HAWK_INCOMING_ACCESS_KEY"),
    "HAWK_INCOMING_SECRET_KEY": env("HAWK_INCOMING_SECRET_KEY"),
}

# GPC Return Address
GPC_RETURN_ADDRESS = env.list("GPC_RETURN_ADDRESS", default=[])

DIT_OFFBOARDING_EMAIL = env("DIT_OFFBOARDING_EMAIL", default="")
JML_TEAM_CONTACT_EMAIL = env("JML_TEAM_CONTACT_EMAIL", default="")
JML_TEAM_EMAILS = env.list("JML_TEAM_EMAILS", default=[])
JML_ONLY_SEND_EMAILS_TO_JML_TEAM = env.bool(
    "JML_ONLY_SEND_EMAILS_TO_JML_TEAM", default=False
)

# Help desk interface
HELP_DESK_INTERFACE = env("HELP_DESK_INTERFACE", default="")
HELP_DESK_CREDS = env.dict("HELP_DESK_CREDS", default={})

# LSD team
LSD_HELP_DESK_LIVE = env.bool("LSD_HELP_DESK_LIVE", default=True)

# getAddress() API
GETADDRESS_TOKEN = env("GETADDRESS_TOKEN")

DIT_ACTIVITY_STREAM_CLIENT_CLASS = (
    "core.activity_stream.client.ActivityStreamLeavingRequestClient"
)

# Content
JML_LEAVING_DIT_GUIDANCE_URL = env("JML_LEAVING_DIT_GUIDANCE_URL", default="")
DIT_LOANS_GUIDANCE_URL = env("DIT_LOANS_GUIDANCE_URL", default="")
PERFORMANCE_REVIEW_URL = env("PERFORMANCE_REVIEW_URL", default=None)
DIT_EXPERIENCE_SURVEY = env("DIT_EXPERIENCE_SURVEY", default=None)
TRANSFER_TO_OGD_URL = env("TRANSFER_TO_OGD_URL", default=None)
CHANGE_EMPLOYEES_LM_LINK = env("CHANGE_EMPLOYEES_LM_LINK", default=None)

# Custom DebugPy setting
ENABLE_DEBUGPY = env.bool("ENABLE_DEBUGPY", False)
