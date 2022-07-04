import logging
from typing import Any, Dict, Iterable, Iterator, List, Optional
from urllib.parse import urlencode, urlparse, urlunparse

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class ServiceNowException(Exception):
    def __init__(
        self, *args: object, status_code: int, path: str, query: Dict[str, Any]
    ) -> None:
        super().__init__(*args)
        self.status_code = status_code
        self.path = path
        self.query = query

    def __str__(self) -> str:
        path_with_query = self.path + "?" + urlencode(self.query)
        return super().__str__() + f" (HTTP {self.status_code} {path_with_query})"


class ServiceNowResults(Iterator):
    current_index: int = 0
    items: List[Any] = []
    current_url: Optional[str] = None
    next_url: Optional[str] = None

    def __init__(
        self,
        url: str,
        path: str,
        sysparm_query: Optional[str] = None,
        sysparm_fields: Optional[List[str]] = None,
    ) -> None:
        super().__init__()

        self.url = url
        self.path = path
        # Initialize the iterator by making the first call to the API.
        self.url_parts = list(urlparse(self.url + self.path))
        self.query: Dict[str, Any] = {
            "sysparm_limit": 100,
            "sysparm_offset": 0,
        }
        if sysparm_fields:
            self.query["sysparm_fields"] = ",".join(sysparm_fields)
        if sysparm_query:
            self.query["sysparm_query"] = sysparm_query

    def __iter__(
        self,
    ):
        # Build the current URL
        self.url_parts[4] = urlencode(self.query)
        self.current_url = urlunparse(self.url_parts)

        self.call_api()
        return self

    def __next__(self) -> Any:
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

        # Make request
        response = requests.get(self.current_url)
        if response.status_code != 200:
            # Note: Do not include query_url in the error message, as it
            # contains the username and password.
            service_now_exception = ServiceNowException(
                "Failed to get results from Service Now API",
                status_code=response.status_code,
                path=self.path,
                query=self.query,
            )
            logger.exception(service_now_exception)
            raise service_now_exception

        content = response.json()
        content_results = content.get("result", [])
        if not content_results:
            raise StopIteration

        self.items = content_results

        # Build the next URL
        self.query["sysparm_offset"] += 100
        self.url_parts[4] = urlencode(self.query)
        self.next_url = urlunparse(self.url_parts)


class ServiceNowClient:
    def __init__(self) -> None:
        if not settings.SERVICE_NOW_API_URL:
            raise ValueError("SERVICE_NOW_API_URL is not set")
        self.url = settings.SERVICE_NOW_API_URL

    def get_results(
        self,
        path: str,
        sysparm_query: Optional[str] = None,
        sysparm_fields: Optional[List[str]] = None,
    ) -> Iterable[Any]:
        return ServiceNowResults(
            url=self.url,
            path=path,
            sysparm_query=sysparm_query,
            sysparm_fields=sysparm_fields,
        )

    def post(self, path: str, *args, **kwargs):
        return requests.post(self.url + path, *args, **kwargs)
