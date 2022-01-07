from datetime import date
from typing import TypedDict


class LeaverDetails(TypedDict):
    # Personal details
    first_name: str
    last_name: str
    date_of_birth: date
    contact_email_address: str
    contact_phone: str
    contact_address: str
    # Professional details
    grade: str
    job_title: str
    department: str
    directorate: str
    email_address: str
    manager: str
    staff_id: str
    # Misc.
    photo: str


class LeaverDetailUpdates(TypedDict, total=False):
    # Personal details
    first_name: str
    last_name: str
    date_of_birth: date
    contact_email_address: str
    contact_phone: str
    contact_address: str
    # Professional details
    grade: str
    job_title: str
    department: str
    directorate: str
    email_address: str
    manager: str
    staff_id: str
