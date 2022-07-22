from typing import Optional, TypedDict

from core.uksbs.types import PersonData


class LeaverDetails(TypedDict):
    first_name: str
    last_name: str
    contact_email_address: str
    job_title: str
    directorate: str
    staff_id: str
    # Misc.
    photo: str


class LeaverDetailUpdates(TypedDict, total=False):
    first_name: str
    last_name: str
    contact_email_address: str
    job_title: str
    directorate: str


class DisplayScreenEquipmentAsset(TypedDict):
    uuid: str
    name: str


class CirrusAsset(TypedDict):
    uuid: str
    sys_id: Optional[str]
    tag: Optional[str]
    name: str


class LeavingRequestLineReportLineManager(TypedDict):
    name: str
    email: str


class LeavingRequestLineReport(TypedDict):
    uuid: str
    name: str
    email: str
    line_manager: Optional[LeavingRequestLineReportLineManager]
    person_data: Optional[PersonData]
    new_line_report: bool
