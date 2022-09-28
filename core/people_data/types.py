from dataclasses import dataclass
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class PeopleDataResult(DataClassJsonMixin):
    email_address: str
    # NEVER EXPOSE THIS FIELD
    person_id: Optional[str]
    employee_numbers: List[str]
    person_type: Optional[str]
    grade: Optional[str]
    grade_level: Optional[str]
