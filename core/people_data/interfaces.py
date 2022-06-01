from abc import ABC, abstractmethod
import psycopg2

from django.db import connection

from core.people_data import types


class PeopleDataBase(ABC):
    @abstractmethod
    def get_people_data(self, sso_legacy_id: str) -> types.PeopleData:
        raise NotImplementedError


class PeopleDataStubbed(PeopleDataBase):
    def get_people_data(self, sso_legacy_id: str) -> types.PeopleData:
        return {
            # Legacy style SSO user ids
            "employee_numbers": [1, ],
        }


class PeopleDataInterface(PeopleDataBase):
    def get_people_data(self, sso_legacy_id: str) -> types.PeopleData:
        with connections["people_data"].cursor() as cursor:
            # No speech marks in query to avoid SQL injection
            cursor.execute("SELECT employee_numbers FROM dit.people_data__identities WHERE sso_user_id = %s", [sso_legacy_id])
            if cursor.rowcount > 0:
                row = cursor.fetchone()
                return {
                    "employee_numbers": row["employee_numbers"]
                }

        return {
            "employee_numbers": [],
        }
