from abc import ABC, abstractmethod

from django.db import connections

from core.people_data import types


class PeopleDataBase(ABC):
    @abstractmethod
    def get_people_data(self, sso_legacy_id: str) -> types.PeopleData:
        raise NotImplementedError


class PeopleDataStubbed(PeopleDataBase):
    def get_people_data(self, sso_legacy_id: str) -> types.PeopleData:
        result: types.PeopleData = {
            # Legacy style SSO user ids
            "employee_numbers": [
                "1",
            ],
            # NEVER EXPOSE THIS FIELD
            "uksbs_person_id": "123",
        }
        return result


class PeopleDataInterface(PeopleDataBase):
    def get_people_data(self, sso_legacy_id: str) -> types.PeopleData:
        result: types.PeopleData = {
            "employee_numbers": [],
            # NEVER EXPOSE THIS FIELD
            "uksbs_person_id": None,
        }

        with connections["people_data"].cursor() as cursor:
            # No speech marks in query to avoid SQL injection
            cursor.execute(
                (
                    "SELECT employee_numbers, person_id "
                    "FROM dit.people_data__identities "
                    "WHERE sso_user_id = %s"
                ),
                [sso_legacy_id],
            )
            row = cursor.fetchone()

            if row:
                result["employee_numbers"] = row[0]
                result["uksbs_person_id"] = row[1]

        return result
