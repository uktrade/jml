from typing import TYPE_CHECKING, Iterable, List

from activity_stream.models import ActivityStreamStaffSSOUser
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    StaffDocument,
    consolidate_staff_documents,
    get_staff_document_from_staff_index,
)
from leavers.models import LeavingRequest, TaskLog
from leavers.types import LeaverDetails

if TYPE_CHECKING:
    from leavers.workflow.tasks import EmailIds
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
        sso_email_user_id=leaving_request.leaver_activitystream_user.email_user_id,
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
        "directorate": "",
        "staff_id": consolidated_staff_document["staff_id"],
        # Misc.
        "photo": consolidated_staff_document["photo"],
    }
    return leaver_details


def get_email_task_logs(
    *, leaving_request: LeavingRequest, email_id: "EmailIds"
) -> List[TaskLog]:
    all_email_task_logs: Iterable[TaskLog] = leaving_request.email_task_logs.all()
    email_task_logs: List[TaskLog] = []
    for email_task in all_email_task_logs:
        if email_id.value == email_task.task_name:
            email_task_logs.append(email_task)
    return email_task_logs
