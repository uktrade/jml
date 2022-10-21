from dataclasses import dataclass
from typing import List, Optional, TypedDict

from dataclasses_json import DataClassJsonMixin


class PeopleData(TypedDict):
    email_address: str
    employee_numbers: List[str]
    # NEVER EXPOSE THIS FIELD
    uksbs_person_id: Optional[str]


@dataclass
class PeopleDataResult(DataClassJsonMixin):
    """People Data report fields."""

    email_address: str
    # NEVER EXPOSE THIS FIELD
    person_id: Optional[str]
    employee_numbers: List[str]
    person_type: Optional[str]
    grade: Optional[str]
    grade_level: Optional[str]
