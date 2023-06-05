from typing import TYPE_CHECKING, List, Optional
from uuid import uuid4

from django.conf import settings

from activity_stream.models import ActivityStreamStaffSSOUser
from core.uksbs import get_uksbs_interface
from core.uksbs.types import PersonData, PersonHierarchyData
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    StaffDocument,
    StaffDocumentNotFound,
    TooManyStaffDocumentsFound,
    consolidate_staff_documents,
    get_staff_document_from_staff_index,
)
from leavers.exceptions import LeaverDoesNotHaveUKSBSPersonId
from leavers.models import LeavingRequest
from leavers.types import LeavingRequestLineReport

if TYPE_CHECKING:
    from leavers.types import LeaverDetails
    from user.models import User


def update_or_create_leaving_request(
    *, leaver: ActivityStreamStaffSSOUser, user_requesting: "User", **kwargs
) -> LeavingRequest:
    defaults = {
        "user_requesting": user_requesting,
    }
    defaults.update(**kwargs)

    leaving_request, _ = LeavingRequest.objects.prefetch_related().update_or_create(
        leaver_activitystream_user=leaver,
        defaults=defaults,
    )

    # If SERVICE_NOW_ENABLE_ONLINE_PROCESS is false, we need to flag the
    # LeavingRequest as using the offline process.
    if (
        not settings.SERVICE_NOW_ENABLE_ONLINE_PROCESS
        and not leaving_request.service_now_offline
    ):
        leaving_request.service_now_offline = True
        leaving_request.save(update_fields=["service_now_offline"])

    return leaving_request


def get_leaver_details(leaving_request: LeavingRequest) -> "LeaverDetails":
    staff_document: StaffDocument = get_staff_document_from_staff_index(
        sso_email_user_id=leaving_request.leaver_activitystream_user.email_user_id,
    )
    consolidated_staff_document: ConsolidatedStaffDocument = (
        consolidate_staff_documents(
            staff_documents=[staff_document],
        )[0]
    )

    assert leaving_request.leaver_activitystream_user.employee_numbers

    leaver_details: "LeaverDetails" = {
        # Personal details
        "first_name": consolidated_staff_document["first_name"],
        "last_name": consolidated_staff_document["last_name"],
        "contact_email_address": consolidated_staff_document["contact_email_address"],
        # Professional details
        "job_title": consolidated_staff_document["job_title"],
        # TODO: [JMLL-1100] We need to find the current employee number.
        "staff_id": leaving_request.leaver_activitystream_user.employee_numbers[0],
        # Misc.
        "photo": consolidated_staff_document["photo"],
    }
    return leaver_details


def initialise_line_reports(leaving_request: LeavingRequest) -> None:
    if not leaving_request.line_reports:
        uksbs_interface = get_uksbs_interface()
        leaver_as_user: ActivityStreamStaffSSOUser = (
            leaving_request.leaver_activitystream_user
        )
        leaver_person_id = leaver_as_user.get_person_id()
        if not leaver_person_id:
            raise LeaverDoesNotHaveUKSBSPersonId()

        leaver_hierarchy_data: PersonHierarchyData = uksbs_interface.get_user_hierarchy(
            person_id=leaver_person_id,
        )
        person_data_line_reports: List[PersonData] = leaver_hierarchy_data.get(
            "report", []
        )

        lr_line_reports: List[LeavingRequestLineReport] = []
        for line_report in person_data_line_reports:
            if not all(
                [
                    line_report["email_address"],
                    line_report["person_id"],
                    line_report["employee_number"],
                ]
            ):
                continue

            consolidated_staff_document: Optional[ConsolidatedStaffDocument] = None
            try:
                staff_document = get_staff_document_from_staff_index(
                    sso_email_address=line_report["email_address"]
                )
                consolidated_staff_document = consolidate_staff_documents(
                    staff_documents=[staff_document]
                )[0]
            except (StaffDocumentNotFound, TooManyStaffDocumentsFound):
                pass
            lr_line_reports.append(
                {
                    "uuid": str(uuid4()),
                    "name": line_report["full_name"],
                    "email": line_report["email_address"],
                    "line_manager": None,
                    "person_data": line_report,
                    "consolidated_staff_document": consolidated_staff_document,
                }
            )

        leaving_request.line_reports = lr_line_reports
        leaving_request.save(update_fields=["line_reports"])
