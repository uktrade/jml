import requests
from django.conf import settings


def get_sso_user_details(email):
    response = requests.get(
        f"{settings.SSO_API_URL}/user/introspect/?TODO=query_params"
    )

    response.json()

    return {}
