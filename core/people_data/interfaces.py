from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

from django.db import connections
from django.db.backends.utils import CursorWrapper

from core.people_data import types


class PeopleDataBase(ABC):
    @abstractmethod
    def get_people_data(self, email_address: str) -> types.PeopleDataResult:
        raise NotImplementedError


class PeopleDataStubbed(PeopleDataBase):
    def get_people_data(self, email_address: str) -> types.PeopleDataResult:
        people_data_result = types.PeopleDataResult(
            email_address=email_address,
            # NEVER EXPOSE THIS FIELD
            person_id="123",
            employee_numbers=[
                "1",
            ],
            person_type=None,
            grade=None,
            grade_level=None,
        )
        return people_data_result


def row_to_dict(*, cursor: CursorWrapper, row: Tuple) -> Dict[str, Any]:
    return dict(zip([col[0] for col in cursor.description], row))


class PeopleDataInterface(PeopleDataBase):
    def get_people_data(self, email_address: str) -> types.PeopleDataResult:
        people_data_result = types.PeopleDataResult(
            email_address=email_address,
            # NEVER EXPOSE THIS FIELD
            person_id=None,
            employee_numbers=[],
            person_type=None,
            grade=None,
            grade_level=None,
        )

        with connections["people_data"].cursor() as cursor:
            # No speech marks in query to avoid SQL injection
            cursor.execute(
                "SELECT * FROM dit.people_data__jml WHERE email_address = %s",
                [email_address],
            )
            row = cursor.fetchone()
            if row:
                dict_row = row_to_dict(cursor=cursor, row=row)
                people_data_result = types.PeopleDataResult.from_dict(dict_row)

        return people_data_result
