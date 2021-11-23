from abc import ABC, abstractmethod
from typing import Optional, TypedDict

import requests
from django.conf import settings


class SSOUserDetail(TypedDict):
    first_name: str
    last_name: str
    sso_id: str


class StaffSSOBase(ABC):
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
    def get_user_details(self, email: str) -> Optional[SSOUserDetail]:
        response = requests.get(
            f"{settings.SSO_API_URL}/user/introspect/?email={email}"
        )
        if response.ok:
            user_details = response.json()
            return {
                "first_name": user_details["first_name"],
                "last_name": user_details["last_name"],
                "sso_id": user_details["user_id"],
            }
        return None
