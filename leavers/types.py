from typing import TYPE_CHECKING, Optional, TypedDict

from django.db.models.enums import TextChoices

if TYPE_CHECKING:
    from core.uksbs.types import PersonData


class SecurityClearance(TextChoices):
    """
    Security Clearance levels
    """

    BPSS = "bpss", "Baseline Personnel Security Standard (BPSS)"
    CTC = "ctc", "Counter Terrorist Check (CTC)"
    SC = "sc", "Security Check (SC)"
    ESC = "esc", "Enhanced Security Check (eSC)"
    DV = "dv", "Developed Vetting (DV)"
    EDV = "edv", "Enhanced Developed Vetting (eDV)"


class StaffType(TextChoices):
    CIVIL_SERVANT = "civil_servant", "Civil servant"
    FAST_STREAMERS = "fast_streamers", "Fast streamers"
    CONTRACTOR = "contractor", "Contractor"
    BENCH_CONTRACTOR = "bench_contractor", "Bench contractor"


class ReturnOptions(TextChoices):
    OFFICE = "office", "Return to the office"
    HOME = "home", "Home collection"


class LeaverDetails(TypedDict):
    first_name: str
    last_name: str
    contact_email_address: str
    job_title: str
    staff_id: str
    # Misc.
    photo: str


class LeaverDetailUpdates(TypedDict, total=False):
    first_name: str
    last_name: str
    contact_email_address: str
    job_title: str


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
    person_data: Optional["PersonData"]


class ReminderEmailDict(TypedDict):
    day_after_lwd: Optional[str]
    two_days_after_lwd: Optional[str]
    on_ld: Optional[str]
    one_day_after_ld: Optional[str]
    two_days_after_ld_lm: Optional[str]
    two_days_after_ld_proc: Optional[str]


class TaskNote(TypedDict):
    datetime: str
    full_name: str
    note: str
