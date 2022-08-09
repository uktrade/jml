from typing import TYPE_CHECKING, List, Optional, TypedDict

from django.db.models.enums import TextChoices

if TYPE_CHECKING:
    from core.uksbs.types import PersonData
    from leavers.models import TaskLog
    from leavers.workflow.tasks import EmailIds


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
    CONTRACTOR = "contractor", "Contractor such as Green Park"
    BENCH_CONTRACTOR = "bench_contractor", "Bench contractor such as Profusion"


class ReturnOptions(TextChoices):
    OFFICE = "office", "Return to the office"
    HOME = "home", "Home collection"


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
    person_data: Optional["PersonData"]
    new_line_report: bool


class ReminderEmailDict(TypedDict):
    day_after_lwd: "EmailIds"
    two_days_after_lwd: "EmailIds"
    on_ld: "EmailIds"
    one_day_after_ld: "EmailIds"
    two_days_after_ld_lm: "EmailIds"
    two_days_after_ld_proc: "EmailIds"


class LeavingRequestReminderEmailTasks(TypedDict):
    day_after_lwd: List["TaskLog"]
    two_days_after_lwd: List["TaskLog"]
    on_ld: List["TaskLog"]
    one_day_after_ld: List["TaskLog"]
    two_days_after_ld_lm: List["TaskLog"]
    two_days_after_ld_proc: List["TaskLog"]
