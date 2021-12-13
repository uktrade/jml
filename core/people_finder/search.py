import urllib.parse
from typing import Any, List, Optional, TypedDict

import requests
from django.conf import settings
from mohawk import Sender

CONTENT_TYPE = "application/json"


class SearchResult(TypedDict):
    first_name: str
    last_name: str
    photo: Optional[str]
    email: str
    grade: str
    primary_phone_number: str
    roles: List[Any]
    manager: str


def get_search_results(search_term) -> List[SearchResult]:
    safe_search_term = urllib.parse.quote_plus(search_term)
    url = (
        f"{settings.PEOPLE_FINDER_URL}/api/people-search/"
        f"?search_query={safe_search_term}"
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
