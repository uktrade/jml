import os
from pathlib import Path
import environ
from django.urls import reverse_lazy
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
env.read_env()

APP_ENV = env("APP_ENV")

DEBUG = env.bool("DEBUG", default=False)

SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

VCAP_SERVICES = env.json('VCAP_SERVICES', {})

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "sass_processor",
    "django_workflow_engine",
    "django_celery_beat",
    "django_celery_results",
    "authbroker_client",
    "rest_framework",
    "leavers",
    "user",
    "core",
    "core.staff_sso",
    "api",
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
                "django_settings_export.settings_export",
                "dev_tools.views.dev_tools_context",
            ]
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

VCAP_SERVICES = env.json('VCAP_SERVICES', default={})

if 'postgres' in VCAP_SERVICES:
    DATABASE_URL = VCAP_SERVICES['postgres'][0]['credentials']['uri']
else:
    DATABASE_URL = os.getenv('DATABASE_URL')

DATABASES = {
    "default": env.db()
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},  # noqa
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
LOGIN_REDIRECT_URL = "/" #"leavers:leavers_form"

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
    str(BASE_DIR / 'node_modules'),
]

GTM_CODE = env("GTM_CODE", default=None)

SETTINGS_EXPORT = [
    'DEBUG',
    'GTM_CODE',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'authbroker_client.middleware.ProtectAllViewsMiddleware',
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "user.backends.CustomAuthbrokerBackend",
]

DEV_TOOLS_ENABLED = APP_ENV in ("local", "dev")

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
    }
}

# Dev tools
LOGIN_URL = reverse_lazy("dev_tools:index")

SLACK_API_TOKEN = env("SLACK_API_TOKEN", default=None)
SLACK_SRE_CHANNEL_ID = env("SLACK_SRE_CHANNEL_ID", default=None)

# Hawk
PEOPLE_FINDER_HAWK_ACCESS_ID = env("PEOPLE_FINDER_HAWK_ACCESS_ID")
PEOPLE_FINDER_HAWK_SECRET_KEY = env("PEOPLE_FINDER_HAWK_SECRET_KEY")

# People Finder
PEOPLE_FINDER_URL = env("PEOPLE_FINDER_URL")
PEOPLE_FINDER_INTERFACE = env("PEOPLE_FINDER_INTERFACE")

# Staff SSO
STAFF_SSO_INTERFACE = env("STAFF_SSO_INTERFACE", default=None)
STAFF_SSO_ACTIVITY_STREAM_URL = env("STAFF_SSO_ACTIVITY_STREAM_URL", default=None)
STAFF_SSO_ACTIVITY_STREAM_ID = env("STAFF_SSO_ACTIVITY_STREAM_ID", default=None)
STAFF_SSO_ACTIVITY_STREAM_SECRET = env("STAFF_SSO_ACTIVITY_STREAM_SECRET", default=None)

# django-workflow-engine
DJANGO_WORKFLOWS = {
    "leaving": "leavers.workflow.leaving.LeaversWorkflow",
}

# Service Now
SERVICE_NOW_INTERFACE = env("SERVICE_NOW_INTERFACE", default=None)

SITE_URL = env("SITE_URL")

# Legacy People Finder
LEGACY_PEOPLE_FINDER_ES_INDEX = env("LEGACY_PEOPLE_FINDER_ES_INDEX")
LEGACY_PEOPLE_FINDER_ES_URL = env("LEGACY_PEOPLE_FINDER_ES_URL")
