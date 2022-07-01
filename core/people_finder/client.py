import logging
import urllib.parse
from typing import Any, Iterator, List, Optional, TypedDict

import requests
from django.conf import settings
from mohawk import Sender

logger = logging.getLogger(__name__)


class FailedToGetPeopleRecords(Exception):
    pass


class Person(TypedDict):
    first_name: str
    last_name: str
    photo: Optional[str]
    photo_small: Optional[str]
    email: str
    grade: str
    primary_phone_number: str
    roles: List[Any]


def get_sender(url):
    return Sender(
        {
            "id": settings.PEOPLE_FINDER_HAWK_ACCESS_ID,
            "key": settings.PEOPLE_FINDER_HAWK_SECRET_KEY,
            "algorithm": "sha256",
        },
        url,
        "GET",
        content="",
        content_type="",
        always_hash_content=False,
    )


class PeopleFinderIterator(Iterator):
    current_index: int = 0
    items: List[Person] = []
    current_url: Optional[str] = None
    next_url: Optional[str] = None

    def __iter__(self) -> Iterator:
        # Initialize the iterator by making the first call to the API.
        self.current_url = f"{settings.PEOPLE_FINDER_URL}/peoplefinder/api/person-api/"
        self.call_api()
        return self

    def __next__(self) -> Person:
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

        sender = get_sender(self.current_url)
        response = requests.get(
            self.current_url,
            headers={"Authorization": sender.request_header, "Content-Type": ""},
        )

        if response.status_code != 200:
            logger.error(
                f"{response.status_code} response from People Finder API - '{self.current_url}'"
            )
            raise FailedToGetPeopleRecords()

        data = response.json()
        self.items = data.get("results", [])
        self.next_url = data.get("next")


def get_details(legacy_sso_user_id) -> Person:
    safe_id = urllib.parse.quote_plus(legacy_sso_user_id)
    url = f"{settings.PEOPLE_FINDER_URL}/peoplefinder/api/person-api/{safe_id}/"

    sender = get_sender(url)
    response = requests.get(
        url,
        headers={"Authorization": sender.request_header, "Content-Type": ""},
    )

    if response.status_code != 200:
        logger.error(
            f"{response.status_code} response from People Finder API - '{url}'"
        )
        raise FailedToGetPeopleRecords()

    return response.json()
