import json
import logging
import urllib.parse
from typing import Iterator, List, Optional, TypedDict

import requests
from django.conf import settings
from mohawk import Sender

logger = logging.getLogger(__name__)


class FailedToGetPersonRecord(Exception):
    pass


class Role(TypedDict):
    role: str
    team_name: str
    team_id: int
    leader: bool


class Person(TypedDict):
    sso_user_id: Optional[str]
    first_name: str
    last_name: str
    roles: List[Role]
    email: str
    primary_phone_number: Optional[str]
    grade: Optional[str]
    photo: Optional[str]
    photo_small: Optional[str]


def get_sender(url, content_type):
    return Sender(
        {
            "id": settings.PEOPLE_FINDER_HAWK_ACCESS_ID,
            "key": settings.PEOPLE_FINDER_HAWK_SECRET_KEY,
            "algorithm": "sha256",
        },
        url,
        "GET",
        content="",
        content_type=content_type,
    )


class PeopleFinderIterator(Iterator):
    current_index: int = 0
    items: List[Person] = []
    current_url: Optional[str] = None
    next_url: Optional[str] = None

    def __iter__(self) -> Iterator:
        # Initialise the iterator by making the first call to the API.
        self.current_url = f"{settings.PEOPLE_FINDER_URL}/peoplefinder/api/person-api/"
        try:
            self.call_api()
        except StopIteration:
            pass
        return self

    def __next__(self) -> Person:
        value = self.get_next_item()
        self.current_index += 1
        return value

    def get_next_item(self) -> Person:
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

    def next_page(self) -> None:
        if not self.next_url or self.current_url == self.next_url:
            raise StopIteration
        self.current_url = self.next_url

    def call_api(self) -> None:
        if not self.current_url:
            raise StopIteration

        self.current_index = 0

        content_type = "application/json"
        sender = get_sender(self.current_url, content_type)
        response = requests.get(
            self.current_url,
            headers={
                "Authorization": sender.request_header,
                "Content-Type": content_type,
            },
        )

        if response.status_code != 200:
            logger.error(
                f"{response.status_code} response from People Finder API - '{self.current_url}'"
            )
            raise FailedToGetPersonRecord()

        data = response.json()
        self.items = data.get("results", [])
        self.next_url = data.get("next")


def get_details(sso_legacy_user_id) -> Person:
    safe_id = urllib.parse.quote_plus(sso_legacy_user_id)
    url = f"{settings.PEOPLE_FINDER_URL}/peoplefinder/api/person-api/{safe_id}/"

    content_type = "application/json"
    sender = get_sender(url, content_type)
    response = requests.get(
        url,
        headers={"Authorization": sender.request_header, "Content-Type": content_type},
    )

    if response.status_code != 200:
        logger.error(
            f"{response.status_code} response from People Finder API - '{url}'"
        )
        raise FailedToGetPersonRecord()

    try:
        logger.info("People Finder response: ")
        logger.info(response.json())
        return response.json()
    except json.decoder.JSONDecodeError:
        raise FailedToGetPersonRecord(
            f"Could not parse JSON, response content: {str(response.content)}",
        )
