from datetime import date
from typing import Optional, TypedDict


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


class DisplayScreenEquipmentAsset(TypedDict):
    uuid: str
    name: str


class CirrusAsset(TypedDict):
    uuid: str
    sys_id: str
    tag: Optional[str]
    name: str
