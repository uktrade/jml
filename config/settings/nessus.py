from config.settings.base import *  # type: ignore # noqa

INSTALLED_APPS += [  # type: ignore
    "nessus",
]

NESSUS_TEST_ENABLED = True
NESSUS_TEST_USER_PASSWORD = os.environ.get("NESSUS_TEST_USER_PASSWORD")

NESSUS_TEST_USER = {
    "username": "nessus_test",
    "email": "nessus_test@nessus_test.com",
    "sso_contact_email": "nessus_test@nessus_test.com",
    "first_name": "Nessus",
    "last_name": "Test",
    "sso_legacy_user_id": "SSO Legacy ID",
    "sso_email_user_id": "nessus_test@nessus_test.com",
}

AUTHENTICATION_BACKENDS.remove("user.backends.CustomAuthbrokerBackend")
MIDDLEWARE.remove("authbroker_client.middleware.ProtectAllViewsMiddleware")

LOGIN_URL = "/"
