import logging
from abc import ABC, abstractmethod

from core.uksbs.client import UKSBSClient
from core.uksbs.types import LeavingData, PersonHierarchyData

logger = logging.getLogger(__name__)


class UKSBSUserNotFound(Exception):
    pass


class UKSBSBase(ABC):
    @abstractmethod
    def get_user_hierarchy(self, person_id: str) -> PersonHierarchyData:
        raise NotImplementedError

    @abstractmethod
    def submit_leaver_form(self, data: LeavingData) -> None:
        raise NotImplementedError


class UKSBSStubbed(UKSBSBase):
    def get_user_hierarchy(self, person_id: str) -> PersonHierarchyData:
        return {
            "manager": [
                {
                    "person_id": person_id + "manager",
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
                    "person_id": person_id,
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
                    "person_id": person_id + "report1",
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
                    "person_id": person_id + "report2",
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

    def get_user_hierarchy(self, person_id: str) -> PersonHierarchyData:
        """
        Get the person hierarchy data for given person_id.

        Note: person_id is sensitive data, never expose it to an end user or use it in logs.
        """

        return self.client.get_people_hierarchy(person_id=person_id)

    def submit_leaver_form(self, data: LeavingData) -> None:
        """
        Submit the leaver form to inform UK SBS of a leaver.
        """

        self.client.post_leaver_form(data=data)
