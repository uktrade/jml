import requests
from django.conf import settings


def get_sso_user_details(email):
    # response = requests.get(
    #     f"{settings.SSO_API_URL}/user/introspect/?TODO=query_params"
    # )
    #
    # response.json()

    return {
        # TODO - should return all SSO details
        "first_name": "Test",
        "last_name": "Test",
        "sso_id": f"{email}._fake_sso_id",
    }
