from typing import TYPE_CHECKING

from activity_stream.models import ActivityStreamStaffSSOUser
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    StaffDocument,
    consolidate_staff_documents,
    get_staff_document_from_staff_index,
)
from leavers.models import LeavingRequest
from leavers.types import LeaverDetails

if TYPE_CHECKING:
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
    return leaving_request


def get_leaver_details(leaving_request: LeavingRequest) -> LeaverDetails:
    staff_document: StaffDocument = get_staff_document_from_staff_index(
        staff_id=leaving_request.leaver_activitystream_user.identifier,
    )
    consolidated_staff_document: ConsolidatedStaffDocument = (
        consolidate_staff_documents(
            staff_documents=[staff_document],
        )[0]
    )
    leaver_details: LeaverDetails = {
        # Personal details
        "first_name": consolidated_staff_document["first_name"],
        "last_name": consolidated_staff_document["last_name"],
        "contact_email_address": consolidated_staff_document["contact_email_address"],
        # Professional details
        "job_title": consolidated_staff_document["job_title"],
        "directorate": consolidated_staff_document["directorate"],
        "staff_id": consolidated_staff_document["staff_id"],
        # Misc.
        "photo": consolidated_staff_document["photo"],
    }
    return leaver_details
