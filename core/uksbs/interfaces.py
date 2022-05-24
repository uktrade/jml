import logging
from abc import ABC, abstractmethod

from django.conf import settings

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
    def get_user_hierarchy(self, oracle_id: str) -> PersonHierarchyData:
        return {
            "manager": [
                {
                    "person_id": 1,
                    "username": None,
                    "full_name": "Manager 1",
                    "first_name": "Manager",
                    "last_name": "1",
                    "employee_number": "1",
                    "department": "Department 1",
                    "position": "Position 1",
                    "email_address": "manager1@example.com",  # /PS-IGNORE
                    "job_id": 1,
                    "work_phone": None,
                    "work_mobile": None,
                }
            ],
            "employee": [
                {
                    "person_id": 2,
                    "username": None,
                    "full_name": "Employee 1",
                    "first_name": "Employee",
                    "last_name": "1",
                    "employee_number": "2",
                    "department": "Department 1",
                    "position": "Position 2",
                    "email_address": "employee1@example.com",  # /PS-IGNORE
                    "job_id": 2,
                    "work_phone": None,
                    "work_mobile": None,
                }
            ],
            "report": [
                {
                    "person_id": 3,
                    "username": None,
                    "full_name": "Report 1",
                    "first_name": "Report",
                    "last_name": "1",
                    "employee_number": "3",
                    "department": "Department 1",
                    "position": "Position 3",
                    "email_address": "report1@example.com",  # /PS-IGNORE
                    "job_id": 3,
                    "work_phone": None,
                    "work_mobile": None,
                },
                {
                    "person_id": 4,
                    "username": None,
                    "full_name": "Report 2",
                    "first_name": "Report",
                    "last_name": "2",
                    "employee_number": "4",
                    "department": "Department 1",
                    "position": "Position 4",
                    "email_address": "report2@example.com",  # /PS-IGNORE
                    "job_id": 4,
                    "work_phone": None,
                    "work_mobile": None,
                },
            ],
        }

    def submit_leaver_form(self, data: LeavingData) -> None:
        pass


class UKSBSInterface(UKSBSBase):
    def __init__(self) -> None:
        super().__init__()
        self.client = UKSBSClient()

    def get_user_hierarchy(self, oracle_id: str) -> PersonHierarchyData:
        return self.client.get_people_hierarchy(person_id=oracle_id)

    def submit_leaver_form(self, data: LeavingData) -> None:
        if not settings.PROCESS_LEAVING_REQUEST:
            raise Exception(
                "Leaving requests are not currently allowed to be processed, look "
                "at the PROCESS_LEAVING_REQUEST setting for more info."
            )
        self.client.post_leaver_form(data=data)
