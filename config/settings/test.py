from django.urls import reverse_lazy

from config.settings.base import *  # type: ignore # noqa

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEV_TOOLS_ENABLED = True

INSTALLED_APPS += [  # type: ignore
    "dev_tools.apps.DevToolsConfig",
]

LOGIN_URL = reverse_lazy("dev_tools:index")

MIDDLEWARE.append("dev_tools.middleware.DevToolsLoginRequiredMiddleware")  # type: ignore

if "core.middleware.IndexCurrentUser" in MIDDLEWARE:
    MIDDLEWARE.remove("core.middleware.IndexCurrentUser")
