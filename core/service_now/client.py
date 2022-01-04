import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urlparse, urlunparse

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class ServiceNowException(Exception):
    def __init__(
        self, *args: object, status_code: str, path: str, query: Dict[str, Any]
    ) -> None:
        super().__init__(*args)
        self.status_code = status_code
        self.path = path
        self.query = query

    def __str__(self) -> str:
        path_with_query = self.path + "?" + urlencode(self.query)
        return super().__str__() + f" (HTTP {self.status_code} {path_with_query})"


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
    ) -> List[Any]:
        url_parts = list(urlparse(self.url + path))
        query: Dict[str, Any] = {
            "sysparm_limit": 100,
            "sysparm_offset": 0,
        }
        if sysparm_fields:
            query["sysparm_fields"] = ",".join(sysparm_fields)
        if sysparm_query:
            query["sysparm_query"] = sysparm_query

        results = []
        # Loop responses for pagination /PS-IGNORE
        while True:
            # Build URL
            url_parts[4] = urlencode(query)
            query_url = urlunparse(url_parts)
            # Make request
            response = requests.get(query_url)
            if response.status_code != 200:
                # Note: Do not include query_url in the error message, as it
                # contains the username and password.
                service_now_exception = ServiceNowException(
                    "Failed to get results from Service Now API",
                    status_code=response.status_code,
                    path=path,
                    query=query,
                )
                logger.exception(service_now_exception)
                raise service_now_exception
            content = response.json()
            content_results = content.get("result", [])
            if content_results:
                results += content_results
            else:
                break
            query["sysparm_offset"] += 100
        return results

    def post(self, path: str, *args, **kwargs):
        return requests.post(self.url + path, *args, **kwargs)
