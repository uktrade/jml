from datetime import date
from typing import TypedDict


class LeaverDetails(TypedDict):
    first_name: str
    last_name: str
    date_of_birth: date
    contact_email_address: str
    job_title: str
    directorate: str
    staff_id: str
    # Misc.
    photo: str


class LeaverDetailUpdates(TypedDict, total=False):
    first_name: str
    last_name: str
    date_of_birth: date
    contact_email_address: str
    job_title: str
    directorate: str
    staff_id: str
