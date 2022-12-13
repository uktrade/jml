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
    scope: List[str] = ["team-hierarchy-DIT-scope", "leaver-submission-scope"]

    def __init__(self) -> None:
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
        client = BackendApplicationClient(client_id=self.client_id)

        if self.token:
            token_expiry_date = datetime.fromtimestamp(self.token["expires_at"])
            if token_expiry_date > datetime.now():
                return OAuth2Session(
                    client=client,
                    token=self.token,
                    scope=self.scope,
                )

        oauth = OAuth2Session(
            client=client,
            scope=self.scope,
        )
        self.token = oauth.fetch_token(
            token_url=self.token_url,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        return self.get_oauth_session()

    def get_people_hierarchy(self, person_id: str) -> PersonHierarchyData:
        """
        Get the person hierarchy data for given person_id.

        Note: person_id is sensitive data, never expose it to an end user or use it in logs.
        """
        if not settings.UKSBS_HIERARCHY_API_URL:
            raise ValueError("UKSBS_HIERARCHY_API_URL is not set")
        hierarchy_url = settings.UKSBS_HIERARCHY_API_URL
        if not settings.UKSBS_GET_PEOPLE_HIERARCHY:
            raise ValueError("UKSBS_GET_PEOPLE_HIERARCHY is not set")
        path: str = settings.UKSBS_GET_PEOPLE_HIERARCHY
        full_api_url = hierarchy_url + path.format(person_id=person_id)

        oauth_session = self.get_oauth_session()
        response = oauth_session.get(full_api_url)

        if response.status_code != 200:
            raise UKSBSUnexpectedResponse(
                f"UK SBS API returned status code {response.status_code} '{response.content}'"
            )

        data = response.json()
        items: List[PersonHierarchyData] = data.get("items", [])

        if len(items) == 0:
            raise UKSBSPersonNotFound("Person not found")

        item: PersonHierarchyData = items[0]
        error_dict = {"error_msg": "Invalid User"}

        if not item["employee"] or [error_dict] in [
            item["manager"],
            item["employee"],
            item["report"],
        ]:
            raise UKSBSPersonNotFound("Person not found")

        return item

    def post_leaver_form(self, data: LeavingData) -> None:
        if not settings.UKSBS_LEAVER_API_URL:
            raise ValueError("UKSBS_LEAVER_API_URL is not set")
        leaver_submission_url = settings.UKSBS_LEAVER_API_URL
        if not settings.UKSBS_POST_LEAVER_SUBMISSION:
            raise ValueError("UKSBS_POST_LEAVER_SUBMISSION is not set")
        path: str = settings.UKSBS_POST_LEAVER_SUBMISSION
        full_api_url = leaver_submission_url + path

        oauth_session = self.get_oauth_session()
        response = oauth_session.post(full_api_url, json=data)

        if response.status_code != 200:
            raise UKSBSUnexpectedResponse(
                f"UK SBS API returned status code {response.status_code}: '{response.content}'"
            )

        try:
            response_data = response.json()
            request_number = response_data["requestnumber"]
        except Exception:
            # Don't worry about this as we are just trying to log the response
            pass
        else:
            logger.debug(f"UK SBS Leaver submission created: {request_number}")
