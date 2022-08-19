from dataclasses import dataclass
from datetime import date
from typing import List, Optional, TypedDict
from uuid import UUID

from dataclasses_json import DataClassJsonMixin


class PeopleData(TypedDict):
    """
    People Data report fields
    """

    employee_numbers: List[str]
    # NEVER EXPOSE THIS FIELD
    uksbs_person_id: Optional[str]


@dataclass
class PeopleDataResult(DataClassJsonMixin):
    uuid: UUID
    person_type: str
    grade_code: str
    grade_name: str
    location: str
    date_exported_from_source: date
    reporting_period_employee_number: str
    full_name: str
    email_address: str
    employee_numbers: List[str]
    sso_user_id: UUID
    person_id: Optional[str]
