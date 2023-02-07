from typing import TYPE_CHECKING, Optional, TypedDict

from django.db.models.enums import TextChoices

if TYPE_CHECKING:
    from core.uksbs.types import PersonData
    from core.utils.staff_index import ConsolidatedStaffDocument


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


class LeavingReason(TextChoices):
    RESIGNATION = "resignation", "Resignation"
    TRANSFER = "transfer", "Transferring to another Civil Service role"
    END_OF_CONTRACT = "end_of_contract", "End of contract"
    RETIREMENT = "retirement", "Retirement"
    ILL_HEALTH_RETIREMENT = "ill_health_retirement", "Retirement due to ill health"
    DISMISSAL = "dismissal", "Dismissal"
    DEATH_IN_SERVICE = "death_in_service", "Death in service"


class StaffType(TextChoices):
    CIVIL_SERVANT = "civil_servant", "Civil servant"
    CONTRACTOR = "contractor", "Contractor (for example, Hays)"
    BENCH_CONTRACTOR = "bench_contractor", "Bench contractor (for example, Profusion)"
    FAST_STREAMERS = "fast_streamers", "Civil Service Fast Stream"
    LOAN = "loan", "Loan"


class ReturnOptions(TextChoices):
    OFFICE = "office", "In-person return at OAB"
    HOME = "home", "Home collection by courier"


class HealthAndSafetyOfficerOptions(TextChoices):
    HEALTH_AND_SAFETY_OFFICER = (
        "health_and_safety_officer",
        "Yes, I am a health and safety officer",
    )
    FLOOR_LIAISON_OFFICER = "floor_liaison_officer", "Yes, I am a floor liaison officer"
    NEITHER = "neither", "No, I am neither"


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
    staff_uuid: str
    name: str
    email: str


class LeavingRequestLineReport(TypedDict):
    uuid: str
    name: str
    email: str
    line_manager: Optional[LeavingRequestLineReportLineManager]
    person_data: Optional["PersonData"]
    consolidated_staff_document: Optional["ConsolidatedStaffDocument"]


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
