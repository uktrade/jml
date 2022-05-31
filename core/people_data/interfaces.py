from abc import ABC, abstractmethod
import psycopg2

from django.db import connection

from core.people_data import types


class PeopleDataBase(ABC):
    @abstractmethod
    def get_people_data(self, sso_legacy_id: str) -> types.StaffIDs:
        raise NotImplementedError


class PeopleDataStubbed(PeopleDataBase):
    def get_people_data(self, sso_legacy_id: str) -> types.StaffIDs:
        return [{
            # Legacy style SSO user ids
            "sso_user_id": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
            "employee_numbers": [1, ],
        }]


class PeopleDataInterface(PeopleDataBase):
    def get_people_data(self, sso_legacy_id: str) -> types.StaffIDs:
        with connections["people_data"].cursor() as cursor:
            # No speech marks in query to avoid SQL injection
            cursor.execute("SELECT employee_numbers FROM dit.people_data__identities WHERE sso_user_id = %s", [sso_legacy_id])
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
