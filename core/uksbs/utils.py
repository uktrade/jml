from typing import List, Literal, Optional, TypedDict, cast

from django.utils import timezone

from activity_stream.models import ActivityStreamStaffSSOUser
from core.uksbs import get_uksbs_interface
from core.uksbs.types import (
    DirectReport,
    LeavingData,
    PersonData,
    ServiceRequestData,
    ServiceRequestDataContact,
    TemplateData,
)
from leavers.forms.line_manager import (
    AnnualLeavePaidOrDeducted,
    DaysHours,
    FlexiLeavePaidOrDeducted,
)
from leavers.models import LeavingRequest


class LeaveDetails(TypedDict):
    leaverPaidUnpaid: str
    annualLeaveUom: Literal["days", "hours"]
    annualLeavePaidOrDeducted: Literal["paid", "deducted"]
    annualLeaveDaysPaid: int
    annualLeaveHoursPaid: int
    annualLeaveDaysDeducted: int
    annualLeaveHoursDeducted: int
    flexiPaidOrDeducted: Literal["paid", "deducted"]
    flexiHoursPaid: int
    flexiHoursDeducted: int


def get_leave_details(*, leaving_request: LeavingRequest) -> LeaveDetails:
    annual_leave_days_paid: int = 0
    annual_leave_hours_paid: int = 0
    annual_leave_days_deducted: int = 0
    annual_leave_hours_deducted: int = 0
    flexi_hours_paid: int = 0
    flexi_hours_deducted: int = 0

    leaver_paid_unpaid = cast(str, leaving_request.leaver_paid_unpaid)

    # ANNUAL LEAVE
    annual_leave_uom = cast(Literal["days", "hours"], leaving_request.annual_leave)
    annual_leave_paid_or_deducted = cast(
        Literal["paid", "deducted"], leaving_request.annual_leave_measurement
    )
    annual_leave_paid: bool = (
        annual_leave_paid_or_deducted == AnnualLeavePaidOrDeducted.PAID.value
    )
    annual_leave_deducted: bool = (
        annual_leave_paid_or_deducted == AnnualLeavePaidOrDeducted.DEDUCTED.value
    )

    annual_number = cast(int, leaving_request.annual_number)

    if annual_leave_uom == DaysHours.DAYS.value:
        if annual_leave_paid:
            annual_leave_days_paid = annual_number
        elif annual_leave_deducted:
            annual_leave_days_deducted = annual_number
    elif annual_leave_uom == DaysHours.HOURS.value:
        if annual_leave_paid:
            annual_leave_hours_paid = annual_number
        elif annual_leave_deducted:
            annual_leave_hours_deducted = annual_number

    # FLEXI LEAVE
    flexi_paid_or_deducted = cast(
        Literal["paid", "deducted"], leaving_request.flexi_leave
    )
    flexi_number = cast(int, leaving_request.flexi_number)

    if flexi_paid_or_deducted == FlexiLeavePaidOrDeducted.PAID.value:
        flexi_hours_paid = flexi_number
    elif flexi_paid_or_deducted == FlexiLeavePaidOrDeducted.DEDUCTED.value:
        flexi_hours_deducted = flexi_number

    return {
        "leaverPaidUnpaid": leaver_paid_unpaid,
        "annualLeavePaidOrDeducted": annual_leave_paid_or_deducted,
        "annualLeaveUom": annual_leave_uom,
        "annualLeaveDaysPaid": annual_leave_days_paid,
        "annualLeaveHoursPaid": annual_leave_hours_paid,
        "annualLeaveDaysDeducted": annual_leave_days_deducted,
        "annualLeaveHoursDeducted": annual_leave_hours_deducted,
        "flexiPaidOrDeducted": flexi_paid_or_deducted,
        "flexiHoursPaid": flexi_hours_paid,
        "flexiHoursDeducted": flexi_hours_deducted,
    }


def build_leaving_data_from_leaving_request(
    *, leaving_request: LeavingRequest
) -> LeavingData:
    uksbs_interface = get_uksbs_interface()

    assert leaving_request.leaver_activitystream_user
    assert leaving_request.manager_activitystream_user
    assert leaving_request.leaving_date
    assert leaving_request.last_day
    assert leaving_request.reason_for_leaving

    leaver_as: ActivityStreamStaffSSOUser = leaving_request.leaver_activitystream_user
    manager_as: ActivityStreamStaffSSOUser = leaving_request.manager_activitystream_user

    # Not sure if this is the Oracle ID
    leaver_oracle_id = leaver_as.user_id
    line_manager_oracle_id = manager_as.user_id

    uksbs_leaver_hierarchy = uksbs_interface.get_user_hierarchy(
        oracle_id=leaver_oracle_id,
    )

    uksbs_leaver: PersonData = uksbs_leaver_hierarchy["employee"][0]

    uksbs_leaver_managers: List[PersonData] = uksbs_leaver_hierarchy.get("manager", [])
    uksbs_leaver_manager: Optional[PersonData] = None

    for ulm in uksbs_leaver_managers:
        if ulm["person_id"] == line_manager_oracle_id:
            uksbs_leaver_manager = ulm
            break

    if not uksbs_leaver_manager:
        raise Exception("Could not find line manager in UKSBS hierarchy")

    leaver_full_name = uksbs_leaver["full_name"]

    leaver_contact: ServiceRequestDataContact = {
        "contactNumber": leaver_as.user_id,  # Oracle ID
        "contactType": "EMPLOYEE",
        "contactTypePoint": "EMAIL",
        "contactPrimaryFlag": "N",
    }
    line_manager_contact: ServiceRequestDataContact = {
        "contactNumber": manager_as.user_id,  # Oracle ID
        "contactType": "EMPLOYEE",
        "contactTypePoint": "EMAIL",
        "contactPrimaryFlag": "Y",
    }

    submission_datetime = timezone.now().strftime("%d-%B-%Y %H:%M")

    service_request_data: ServiceRequestData = {
        "problemSummary": f"Leaver Notification Form - {leaver_full_name} - {submission_datetime}",
        "contacts": [leaver_contact, line_manager_contact],
    }

    leave_details = get_leave_details(leaving_request=leaving_request)

    direct_reports: List[DirectReport] = []
    additional_direct_reports: List[DirectReport] = []

    for line_report in leaving_request.line_reports:
        direct_report: DirectReport = {
            "OracleID": line_report["person_data"]["person_id"],
            "EmployeeID": line_report["person_data"]["employee_number"],
            "Name": line_report["name"],
            "Email": line_report["email"],
            "NewManager": line_report["line_manager"]["name"],
            "NewManagerEmail": line_report["line_manager"]["email"],
            "Effectivedate": leaving_request.leaving_date.strftime("%d/%m/%Y %H:%M"),
        }
        if line_report["new_line_report"]:
            additional_direct_reports.append(direct_report)
        else:
            direct_reports.append(direct_report)

    template_data: TemplateData = {
        "additionalDirectReports": additional_direct_reports,
        "directReports": direct_reports,
        # Payroll Details
        "leaverPaidUnpaid": leave_details["leaverPaidUnpaid"],
        "annualLeavePaidOrDeducted": leave_details["annualLeavePaidOrDeducted"],
        "annualLeaveUom": leave_details["annualLeaveUom"],
        "annualLeaveDaysPaid": leave_details["annualLeaveDaysPaid"],
        "annualLeaveHoursPaid": leave_details["annualLeaveHoursPaid"],
        "annualLeaveDaysDeducted": leave_details["annualLeaveDaysDeducted"],
        "annualLeaveHoursDeducted": leave_details["annualLeaveHoursDeducted"],
        "flexiPaidOrDeducted": leave_details["flexiPaidOrDeducted"],
        "flexiHoursPaid": leave_details["flexiHoursPaid"],
        "flexiHoursDeducted": leave_details["flexiHoursDeducted"],
        # Leaver Details
        "leaverName": leaver_full_name,
        "leaverEmail": uksbs_leaver["email_address"],
        "leaverOracleID": str(uksbs_leaver["person_id"]),
        "leaverEmployeeNumber": uksbs_leaver["employee_number"],
        "leaverReasonForLeaving": leaving_request.reason_for_leaving,
        "leaverLastDay": leaving_request.last_day.strftime("%d/%m/%Y %H:%M"),
        # Leaver Correspondance Details
        "newCorrEmail": "",
        "newCorrAddressLine1": "",
        "newCorrAddressLine2": "",
        "newCorrAddressLine3": "",
        "newCorrCounty": "",
        "newCorrPostcode": "",
        "newCorrPhone": "",
        # Submitter Details
        "submitterName": uksbs_leaver_manager["full_name"],
        "submitterEmail": uksbs_leaver_manager["email_address"],
        "submitterOracleID": str(uksbs_leaver_manager["person_id"]),
        "submitterDate": timezone.now().strftime("%d/%m/%Y %H:%M"),
        "submitterSelectedLineManager": uksbs_leaver_manager["full_name"],
        "submitterSelectedLineManagerEmail": uksbs_leaver_manager["email_address"],
        "submitterSelectedLineManagerOracleID": str(uksbs_leaver_manager["person_id"]),
        "submitterSelectedLineManagerEmployeeNumber": uksbs_leaver_manager[
            "employee_number"
        ],
    }

    leaving_data: LeavingData = {
        "serviceRequestData": service_request_data,
        "templateData": template_data,
    }

    return leaving_data