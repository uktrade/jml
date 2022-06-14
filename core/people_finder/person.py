import urllib.parse
from typing import Any, List, Optional, TypedDict

import requests
from django.conf import settings
from mohawk import Sender


CONTENT_TYPE = "application/json"


class Person(TypedDict):
    first_name: str
    last_name: str
    photo: Optional[str]
    photo_small: Optional[str]
    email: str
    grade: str
    primary_phone_number: str
    roles: List[Any]


def get_details(legacy_sso_user_id) -> Person:
    safe_id = urllib.parse.quote_plus(legacy_sso_user_id)
    url = (
        f"{settings.PEOPLE_FINDER_URL}/peoplefinder/api/person-api/{safe_id}/"
    )
    sender = Sender(
        {
            "id": settings.PEOPLE_FINDER_HAWK_ACCESS_ID,
            "key": settings.PEOPLE_FINDER_HAWK_SECRET_KEY,
            "algorithm": "sha256",
        },
        url,
        "GET",
        content="",
        content_type=CONTENT_TYPE,
    )

    response = requests.get(
        url,
        data="",
        headers={"Authorization": sender.request_header, "Content-Type": CONTENT_TYPE},
    )

    return response.json()
