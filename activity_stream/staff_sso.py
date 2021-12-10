from typing import Any, List, Optional, TypedDict

import requests
from django.conf import settings
from mohawk import Sender


URL = settings.STAFF_SSO_ACTIVITY_STREAM_URL
CONTENT_TYPE = "application/json"


def get_sender(*, url: Optional[str] = None) -> Sender:
    return Sender(
        {
            "id": settings.STAFF_SSO_ACTIVITY_STREAM_ID,
            "key": settings.STAFF_SSO_ACTIVITY_STREAM_SECRET,
            "algorithm": "sha256",
        },
        url,
        "GET",
        content="",
        content_type=CONTENT_TYPE,
    )


class FailedToGetActivityStream(Exception):
    pass


OrderedItem = TypedDict(
    "OrderedItem",
    {
        "dit:StaffSSO:User:becameInactiveOn": Optional[Any],
        "dit:StaffSSO:User:contactEmailAddress": Optional[Any],
        "dit:StaffSSO:User:emailUserId": str,
        "dit:StaffSSO:User:joined": str,
        "dit:StaffSSO:User:lastAccessed": str,
        "dit:StaffSSO:User:permittedApplications": List[Any],
        "dit:StaffSSO:User:status": str,
        "dit:StaffSSO:User:userId": str,
        "dit:emailAddress": str,
        "dit:lastName": str,  # /PS-IGNORE
        "dit:firstName": str,  # /PS-IGNORE
        "id": str,
        "name": str,
        "type": str,
    },
)


class ActivityStreamOrderedItems(TypedDict):
    id: str
    object: OrderedItem
    published: str


def get_activity_stream(
    *,
    url: Optional[str] = None,
) -> List[ActivityStreamOrderedItems]:
    if url is None:
        url = URL
    sender = get_sender(url=url)

    response = requests.get(
        url,
        data="",
        headers={"Authorization": sender.request_header, "Content-Type": CONTENT_TYPE},
    )

    if response.status_code != 200:
        raise FailedToGetActivityStream()

    data = response.json()
    activity_stream = data.get("orderedItems", [])

    # If there is a "next" URL, we need to recursively call this function unless
    # the next URL is the current URL
    if "next" in data and data["next"] != url:
        activity_stream += get_activity_stream(url=data["next"])

    return activity_stream
