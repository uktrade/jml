import logging
from typing import Any

from django.conf import settings
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

logger = logging.getLogger(__name__)


class UKSBSClient:
    def __init__(self) -> None:
        if not settings.UKSBS_API_URL:
            raise ValueError("UKSBS_API_URL is not set")
        self.url = settings.UKSBS_API_URL
        if not settings.UKSBS_ACCESS_URL:
            raise ValueError("UKSBS_ACCESS_URL is not set")
        self.access_url = settings.UKSBS_ACCESS_URL
        self.client_id = "your_client_id"
        self.client_secret = "your_client_secret"

    def get_oauth_session(self) -> OAuth2Session:
        client = BackendApplicationClient(client_id=self.client_id)
        oauth = OAuth2Session(client=client)
        token = oauth.fetch_token(
            token_url=self.access_url,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        return OAuth2Session(client=client, token=token)

    def get_people_hierarchy(self, person_id: str) -> Any:
        if not settings.UKSBS_GET_PEOPLE_HIERARCHY:
            raise ValueError("UKSBS_GET_PEOPLE_HIERARCHY is not set")
        path: str = settings.UKSBS_GET_PEOPLE_HIERARCHY
        full_api_url = self.url + path.format(person_id=person_id)

        oauth_session = self.get_oauth_session()
        response = oauth_session.get(full_api_url)
        return response
