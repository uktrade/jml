from typing import List, Optional, TypedDict


class PeopleData(TypedDict):
    """
    People Data report fields
    """

    employee_numbers: List[str]
    # NEVER EXPOSE THIS FIELD
    uksbs_person_id: Optional[str]
