from config.settings.dev import *  # type: ignore # noqa

"""
Local Development Settings

These settings are used when running the project locally.
"""

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


"""
Using SSO locally

Uncomment the below (you must comment out all the Dev Test user settings)
"""

# AUTHBROKER_ANONYMOUS_PATHS = [
#     "/admin/",
#     "/admin/login/",
# ]

"""
Using Dev Test Users locally

Uncomment the below (you must comment out all the SSO settings)
"""

INSTALLED_APPS += [  # type: ignore
    "dev_tools.apps.DevToolsConfig",
]

LOGIN_URL = reverse_lazy("dev_tools:index")

MIDDLEWARE.append("dev_tools.middleware.DevToolsLoginRequiredMiddleware")  # type: ignore
AUTHENTICATION_BACKENDS.remove("user.backends.CustomAuthbrokerBackend")  # type: ignore
MIDDLEWARE.remove("authbroker_client.middleware.ProtectAllViewsMiddleware")  # type: ignore
