import os
import sys

from config.settings.base import *  # type: ignore # noqa

INSTALLED_APPS += [  # type: ignore
    "dev_tools.apps.DevToolsConfig",
]

MIDDLEWARE.append("dev_tools.middleware.DevToolsLoginRequiredMiddleware")  # type: ignore
MIDDLEWARE.remove("authbroker_client.middleware.ProtectAllViewsMiddleware")  # type: ignore
AUTHENTICATION_BACKENDS.remove("user.backends.CustomAuthbrokerBackend")  # type: ignore

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
