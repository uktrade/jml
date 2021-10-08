import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
env.read_env()

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
    "leavers",
    "user",
    "authbroker_client",
    "django_workflow_engine",
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
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"

CAN_ELEVATE_SSO_USER_PERMISSIONS = False
CAN_CREATE_TEST_USER = False

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "sass_processor.finders.CssFinder",
]

STATICFILES_DIRS = [
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

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
    }
}

# django-workflow-engine
DJANGO_WORKFLOWS = [
    "leavers.workflow.LeaversWorkflow",
]
