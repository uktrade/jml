from .dev import *  # type: ignore # noqa

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

AUTHBROKER_ANONYMOUS_PATHS = [
    "/admin/",
    "/admin/login/",
]
