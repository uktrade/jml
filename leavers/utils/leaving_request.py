from typing import TYPE_CHECKING

from django.conf import settings

from activity_stream.models import ActivityStreamStaffSSOUser
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    StaffDocument,
    consolidate_staff_documents,
    get_staff_document_from_staff_index,
)
from leavers.models import LeavingRequest

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
        leaver_complete__isnull=True,
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
