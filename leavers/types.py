from datetime import date
from typing import Optional, TypedDict


class LeaverDetails(TypedDict):
    # Personal details
    first_name: str
    last_name: str
    date_of_birth: date
    personal_email: str
    personal_phone: str
    personal_address: str
    # Professional details
    grade: str
    job_title: str
    department: str
    directorate: str
    work_email: str
    manager: str
    staff_id: str
    # Misc.
    photo: str


class LeaverDetailUpdates(TypedDict, total=False):
    # Personal details
    first_name: str
    last_name: str
    date_of_birth: date
    personal_email: str
    personal_phone: str
    personal_address: str
    # Professional details
    grade: str
    job_title: str
    department: str
    directorate: str
    work_email: str
    manager: str
    staff_id: str
    # Misc.
    photo: str
