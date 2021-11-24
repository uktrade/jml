from datetime import date
from typing import TypedDict


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
    directorate: str
    department: str
    team_name: str
    work_email: str
    manager: str
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
    directorate: str
    department: str
    team_name: str
    work_email: str
    manager: str
    # Misc.
    photo: str
