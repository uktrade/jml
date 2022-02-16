import sys

from config.settings.base import *  # type: ignore # noqa

"""
Development settings

These settings are used by the dev and staging instances.
"""

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
