from typing import Any, Iterator, List, Optional, TypedDict

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


class StaffSSOActivityStreamIterator(Iterator):
    current_index: int = 0
    items: List[ActivityStreamOrderedItems] = []
    current_url: Optional[str] = None
    next_url: Optional[str] = None

    def __iter__(self) -> Iterator:
        # Initialize the iterator by making the first call to the API.
        self.current_url = URL
        self.call_api()
        return self

    def __next__(self) -> ActivityStreamOrderedItems:
        value = self.get_next_item()
        self.current_index += 1
        return value

    def get_next_item(self):
        # If there are no items in the object, stop the iteration.
        if len(self.items) == 0:
            raise StopIteration

        # Get the next item from the object.
        try:
            value = self.items[self.current_index]
        except IndexError:
            # If the index is out of range, move to the next page.
            self.next_page()
            self.call_api()
            value = self.get_next_item()

        return value

    def next_page(self):
        if not self.next_url or self.current_url == self.next_url:
            raise StopIteration
        self.current_url = self.next_url

    def call_api(self):
        if not self.current_url:
            raise StopIteration

        self.current_index = 0

        sender = get_sender(url=self.current_url)

        response = requests.get(
            self.current_url,
            data="",
            headers={
                "Authorization": sender.request_header,
                "Content-Type": CONTENT_TYPE,
            },
        )

        if response.status_code != 200:
            raise FailedToGetActivityStream()

        data = response.json()
        self.items = data.get("orderedItems", [])
        self.next_url = data.get("next")
