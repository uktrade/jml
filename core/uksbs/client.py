import logging
from datetime import datetime
from typing import List, Optional

from django.conf import settings
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

from core.uksbs.types import AccessToken, LeavingData, PersonHierarchyData

logger = logging.getLogger(__name__)


class UKSBSUnexpectedResponse(Exception):
    pass


class UKSBSPersonNotFound(Exception):
    pass


class UKSBSClient:
    token: Optional[AccessToken] = None

    def __init__(self) -> None:
        if not settings.UKSBS_API_URL:
            raise ValueError("UKSBS_API_URL is not set")
        self.url = settings.UKSBS_API_URL

        if not settings.UKSBS_TOKEN_URL:
            raise ValueError("UKSBS_TOKEN_URL is not set")
        self.token_url = settings.UKSBS_TOKEN_URL

        if not settings.UKSBS_CLIENT_ID:
            raise ValueError("UKSBS_CLIENT_ID is not set")
        self.client_id = settings.UKSBS_CLIENT_ID

        if not settings.UKSBS_CLIENT_SECRET:
            raise ValueError("UKSBS_CLIENT_SECRET is not set")
        self.client_secret = settings.UKSBS_CLIENT_SECRET

    def get_oauth_session(self) -> OAuth2Session:
        scope = ["team-hierarchy-DIT-scope"]
        client = BackendApplicationClient(client_id=self.client_id)

        if self.token:
            token_expiry_date = datetime.fromtimestamp(self.token["expires_at"])
            if token_expiry_date > datetime.now():
                return OAuth2Session(
                    client=client,
                    token=self.token,
                    scope=scope,
                )

        oauth = OAuth2Session(
            client=client,
            scope=scope,
        )
        self.token = oauth.fetch_token(
            token_url=self.token_url,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        return self.get_oauth_session()

    def get_people_hierarchy(self, person_id: str) -> PersonHierarchyData:
        if not settings.UKSBS_GET_PEOPLE_HIERARCHY:
            raise ValueError("UKSBS_GET_PEOPLE_HIERARCHY is not set")
        path: str = settings.UKSBS_GET_PEOPLE_HIERARCHY
        full_api_url = self.url + path.format(person_id=person_id)

        oauth_session = self.get_oauth_session()
        response = oauth_session.get(full_api_url)

        if response.status_code != 200:
            raise UKSBSUnexpectedResponse(
                f"UK SBS API returned status code {response.status_code}"
            )

        data = response.json()
        items: List[PersonHierarchyData] = data.get("items", [])

        if len(items) == 0:
            raise UKSBSPersonNotFound("Person not found")

        item: PersonHierarchyData = items[0]
        error_dict = {"error_msg": "Invalid User"}

        if any(
            [
                error_dict in item["manager"],
                error_dict in item["employee"],
                error_dict in item["report"],
            ]
        ):
            raise UKSBSPersonNotFound("Person not found")

        return item

    def post_leaver_form(self, data: LeavingData) -> None:
        if not settings.UKSBS_POST_LEAVER_SUBMISSION:
            raise ValueError("UKSBS_POST_LEAVER_SUBMISSION is not set")
        path: str = settings.UKSBS_POST_LEAVER_SUBMISSION
        full_api_url = self.url + path

        oauth_session = self.get_oauth_session()
        response = oauth_session.post(full_api_url)

        if response.status_code != 200:
            raise UKSBSUnexpectedResponse(
                f"UK SBS API returned status code {response.status_code}"
            )