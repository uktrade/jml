from typing import Optional, TypedDict


class StaffIDs(TypedDict):
    """
    List of staff ids available in People Data report
    """
    sso_user_id: str # Legacy format
    employee_numbers: List[str]
