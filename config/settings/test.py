from config.settings.dev import *  # type: ignore # noqa

INSTALLED_APPS += [  # type: ignore
    "dev_tools.apps.DevToolsConfig",
]

LOGIN_URL = reverse_lazy("dev_tools:index")

MIDDLEWARE.append("dev_tools.middleware.DevToolsLoginRequiredMiddleware")  # type: ignore
AUTHENTICATION_BACKENDS.remove("user.backends.CustomAuthbrokerBackend")  # type: ignore
MIDDLEWARE.remove("authbroker_client.middleware.ProtectAllViewsMiddleware")  # type: ignore
