from abc import ABC, abstractmethod
from typing import Optional, TypedDict

import requests
from authbroker_client.utils import get_client
from django.conf import settings
from django.http.request import HttpRequest
from urllib.parse import urljoin


class SSOUserDetail(TypedDict):
    first_name: str
    last_name: str
    sso_id: str


class StaffSSOBase(ABC):
    def __init__(self, *, request: HttpRequest):
        self.request: HttpRequest = request

    @abstractmethod
    def get_user_details(self, *, email: str) -> Optional[SSOUserDetail]:
        raise NotImplementedError


class StaffSSOStubbed(StaffSSOBase):
    def get_user_details(self, email: str) -> Optional[SSOUserDetail]:
        return {
            "first_name": "Joe",
            "last_name": "Bloggs",
            "sso_id": "123",
        }


class StaffSSOInterface(StaffSSOBase):
    def __init__(self, *args, request: HttpRequest, **kwargs):
        super().__init__(*args, request=request, **kwargs)
        self.client = get_client(request=self.request)

    def get_user_details(self, email: str) -> Optional[SSOUserDetail]:
        user_detail_url = urljoin(settings.AUTHBROKER_URL, f"/api/v1/user/introspect/?email={email}")
        response = self.client.get(user_detail_url)
        if response.ok:
            user_details = response.json()
            return {
                "first_name": user_details["first_name"],
                "last_name": user_details["last_name"],
                "sso_id": user_details["user_id"],
            }
        return None
