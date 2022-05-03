import logging
from abc import ABC, abstractmethod

from core.uksbs.client import UKSBSClient
from core.uksbs.types import LeavingData, PersonHierarchyData

logger = logging.getLogger(__name__)


class UKSBSUserNotFound(Exception):
    pass


class UKSBSBase(ABC):
    @abstractmethod
    def get_user_hierarchy(self, oracle_id: str) -> PersonHierarchyData:
        raise NotImplementedError

    @abstractmethod
    def submit_leaver_form(self, data: LeavingData) -> None:
        raise NotImplementedError


class UKSBSStubbed(UKSBSBase):
    def get_user_hierarchy(self, email: str) -> PersonHierarchyData:
        return {
            "manager": [],
            "employee": [],
            "report": [],
        }

    def submit_leaver_form(self, data: LeavingData) -> None:
        pass


class UKSBSInterface(UKSBSBase):
    def __init__(self, *args, **kwargs):
        self.client = UKSBSClient()

    def get_user_hierarchy(self, oracle_id: str) -> PersonHierarchyData:
        return self.client.get_people_hierarchy(person_id=oracle_id)

    def submit_leaver_form(self, data: LeavingData) -> None:
        self.client.post_leaver_form(data=data)
