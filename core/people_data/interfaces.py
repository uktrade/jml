from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

from django.db import connections
from django.db.backends.utils import CursorWrapper

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


def row_to_dict(*, cursor: CursorWrapper, row: Tuple) -> Dict[str, Any]:
    return dict(zip([col[0] for col in cursor.description], row))


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
                "SELECT * FROM dit.people_data__identities WHERE sso_user_id = %s",
                [sso_legacy_id],
            )
            row = cursor.fetchone()
            if row:
                dict_row = row_to_dict(cursor=cursor, row=row)
                people_data_result = types.PeopleDataResult.from_dict(dict_row)
                result["employee_numbers"] = people_data_result.employee_numbers
                result["uksbs_person_id"] = people_data_result.person_id

        return result
