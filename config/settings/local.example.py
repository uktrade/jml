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


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Data visualisation
GRAPH_MODELS = {
    "all_applications": True,
    "group_models": True,
}
