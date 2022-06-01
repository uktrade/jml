from typing import Optional, TypedDict


class PeopleData(TypedDict):
    """
    People Data report fields
    """
    employee_numbers: Optional[List[str]]
