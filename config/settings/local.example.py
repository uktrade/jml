import sys

from config.settings.base import *  # type: ignore # noqa

"""
Local Development Settings

These settings are used when running the project locally.
"""

INSTALLED_APPS += [  # type: ignore
    "django_extensions",
]

LOGGING["handlers"]["stdout"] = {  # type: ignore
    "class": "logging.StreamHandler",
    "stream": sys.stdout,
}
LOGGING["root"] = {
    "handlers": ["stdout"],
    "level": os.getenv("ROOT_LOG_LEVEL", "INFO"),
}
LOGGING["loggers"] = {
    "django": {
        "handlers": [
            "stdout",
        ],
        "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
        "propagate": True,
    },
}

DATABASES["people_data"] = {
    "HOST": env("PEOPLE_DATA_POSTGRES_HOST"),
    "NAME": env("PEOPLE_DATA_POSTGRES_DATABASE"),
    "PORT": env("PEOPLE_DATA_POSTGRES_PORT", default=5432),
    "ENGINE": "django.db.backends.postgresql",
    "USER": env("PEOPLE_DATA_POSTGRES_USERNAME"),
    "PASSWORD": env("PEOPLE_DATA_POSTGRES_PASSWORD"),
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Data visualisation
GRAPH_MODELS = {
    "all_applications": True,
    "group_models": True,
}

# DebugPy
ENABLE_DEBUGPY = True
