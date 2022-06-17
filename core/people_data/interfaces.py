from abc import ABC, abstractmethod

from django.db import connections

from core.people_data import types


class PeopleDataBase(ABC):
    @abstractmethod
    def get_people_data(self, sso_legacy_id: str) -> types.PeopleData:
        raise NotImplementedError


class PeopleDataStubbed(PeopleDataBase):
    def get_people_data(self, sso_legacy_id: str) -> types.PeopleData:
        return {
            # Legacy style SSO user ids
            "employee_numbers": [
                1,
            ],
        }


class PeopleDataInterface(PeopleDataBase):
    def get_people_data(self, sso_legacy_id: str) -> types.PeopleData:
        with connections["people_data"].cursor() as cursor:
            result = {
                "employee_numbers": [],
            }
            # No speech marks in query to avoid SQL injection
            cursor.execute(
                "SELECT employee_numbers FROM dit.people_data__identities WHERE sso_user_id = %s",
                [sso_legacy_id],
            )
            row = cursor.fetchone()

        if row:
            result["employee_numbers"] = row[0]

        return result
