from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Tuple

from django.db import connections
from django.db.backends.utils import CursorWrapper

from core.people_data import types


class PeopleDataBase(ABC):
    @abstractmethod
    def get_people_data(self, email_address: str) -> types.PeopleDataResult:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> Iterator[types.PeopleData]:
        raise NotImplementedError

    @abstractmethod
    def get_emails_with_multiple_person_ids(self) -> List[str]:
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

    def get_all(self) -> Iterator[types.PeopleData]:
        results: list[types.PeopleData] = [
            {
                "email_address": "test1@example.com",  # /PS-IGNORE
                "employee_numbers": ["1"],
                "uksbs_person_id": "123",
            },
            {
                "email_address": "test2@example.com",  # /PS-IGNORE
                "employee_numbers": ["2", "3"],
                "uksbs_person_id": "124",
            },
        ]

        yield from results

    def get_emails_with_multiple_person_ids(self) -> List[str]:
        return ["test_email1", "test_email2", "miss.marple@example.com"]  # /PS-IGNORE


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

        with connections["default"].cursor() as cursor:
            # No speech marks in query to avoid SQL injection
            cursor.execute(
                "SELECT * FROM data_import__people_data__jml WHERE email_address = %s",
                [email_address],
            )
            row = cursor.fetchone()

        if row:
            dict_row = row_to_dict(cursor=cursor, row=row)
            people_data_result = types.PeopleDataResult.from_dict(
                dict_row,
                infer_missing=True,
            )

        return people_data_result

    def get_all(self, fetchmany_size: int = 500) -> Iterator[types.PeopleData]:
        with connections["default"].cursor() as cursor:
            cursor.execute(
                # If you change the columns here then please don't forget to update the
                # rest of the function!
                "SELECT email_address, employee_numbers, person_id"
                " FROM data_import__people_data__jml"
            )

            while True:
                results = cursor.fetchmany(fetchmany_size)

                if not results:
                    break

                for row in results:
                    # We need to keep this in sync with the SQL query above.
                    people_data: types.PeopleData = {
                        "email_address": row[0],
                        "employee_numbers": row[1],
                        "uksbs_person_id": row[2],
                    }
                    yield people_data

    def get_emails_with_multiple_person_ids(self) -> List[str]:
        with connections["default"].cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    email_address,
                    array_agg(DISTINCT person_id) AS person_ids
                FROM
                    data_import__people_data__jml
                WHERE
                    email_address IS NOT NULL
                    AND email_address != ''
                    AND person_id IS NOT NULL
                GROUP BY
                    email_address
                HAVING
                    array_length(array_agg(DISTINCT person_id), 1) > 1
                """
            )
            rows = cursor.fetchall()
        emails: List[str] = [row[0] for row in rows]
        return emails
