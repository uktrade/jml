import json
import logging
from typing import Any, Dict, Iterator, List, Optional, TypedDict

import requests
from django.conf import settings
from mohawk import Sender

logger = logging.getLogger(__name__)

URL = settings.STAFF_SSO_ACTIVITY_STREAM_URL
CONTENT_TYPE = "application/json"


def hawk_request(method, url, body):
    header = Sender(
        {
            "id": settings.STAFF_SSO_ACTIVITY_STREAM_ID,
            "key": settings.STAFF_SSO_ACTIVITY_STREAM_SECRET,
            "algorithm": "sha256",
        },
        url,
        method,
        content_type="application/json",
        content=body,
    ).request_header

    response = requests.request(
        method,
        url,
        data=body,
        headers={
            "Authorization": header,
            "Content-Type": "application/json",
        },
    )
    return response


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
        "dit:StaffSSO:User:is_active": bool,
        "dit:emailAddress": str,
        "dit:lastName": str,  # /PS-IGNORE
        "dit:firstName": str,  # /PS-IGNORE
        "id": str,
        "name": str,
        "type": str,
    },
)


class ActivityStreamOrderedItem(TypedDict):
    id: str
    object: OrderedItem
    published: str


class StaffSSOActivityStreamIterator(Iterator):
    current_index: int = 0
    items: List[ActivityStreamOrderedItem] = []
    search_after: Dict[Any, Any] = {}

    def __iter__(self) -> Iterator:
        # Initialize the iterator by making the first call to the API.
        self.current_url = URL
        try:
            self.call_api()
        except StopIteration:
            pass
        return self

    def __next__(self) -> ActivityStreamOrderedItem:
        value = self.get_next_item()
        self.current_index += 1
        return value

    def get_next_item(self):
        # If there are no items in the object, stop the iteration.
        if len(self.items) == 0:
            raise StopIteration

        # Get the next item from the object.
        try:
            value = self.items[self.current_index]["_source"]
        except IndexError:
            # If the index is out of range, move to the next page.
            self.call_api()
            value = self.get_next_item()

        return value

    def call_api(self):
        if not self.current_url:
            raise StopIteration

        self.current_index = 0

        response = hawk_request(
            "GET",
            self.current_url,
            json.dumps(
                {
                    "size": 1000,
                    "query": {
                        "match": {"object.type": "dit:StaffSSO:User"},
                    },
                    "sort": [{"published": "asc"}, {"id": "asc"}],
                    **self.search_after,
                }
            ),
        )

        if response.status_code != 200:
            logger.error(
                f"{response.status_code} response from Staff SSO Activity Stream - "
                f"'{self.current_url}'"
            )
            raise FailedToGetActivityStream()

        data = response.json()
        hits = data.get("hits", {})
        self.items = hits.get("hits", [])

        if not self.items:
            raise StopIteration

        self.search_after = {"search_after": self.items[-1]["sort"]}
