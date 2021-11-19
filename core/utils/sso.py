from typing import TypedDict
import requests
from django.conf import settings
from typing import List


class SSOUserDetail(TypedDict):
    first_name: str
    last_name: str
    sso_id: str


def get_sso_user_details(*, email: str) -> SSOUserDetail:
    """
    Get user details from Staff SSO for a given email address
    """
    response = requests.get(
        f"{settings.SSO_API_URL}/user/introspect/?email={email}"
    )
    # TODO: Check if the response was successful
    # TODO: Check data output is correct
    user = response.json()
    return {
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "sso_id": user["user_id"],
    }
