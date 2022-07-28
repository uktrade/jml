from typing import Optional

from django.conf import settings
from django.db.models.query import QuerySet

from activity_stream.models import ActivityStreamStaffSSOUser, ServiceEmailAddress
from core.service_now import get_service_now_interface
from core.service_now.interfaces import ServiceNowUserNotFound
from core.utils.staff_index import (
    StaffDocument,
    StaffDocumentNotFound,
    TooManyStaffDocumentsFound,
    get_staff_document_from_staff_index,
    index_staff_document,
)


def ingest_service_now():
    service_now_interface = get_service_now_interface()

    as_users: QuerySet[
        ActivityStreamStaffSSOUser
    ] = ActivityStreamStaffSSOUser.objects.all()

    for as_staff_sso_user in as_users:
        try:
            staff_document = get_staff_document_from_staff_index(
                sso_email_user_id=as_staff_sso_user.email_user_id,
            )
        except (StaffDocumentNotFound, TooManyStaffDocumentsFound):
            continue

        staff_sso_email: Optional[
            ServiceEmailAddress
        ] = as_staff_sso_user.service_emails.first()

        if not staff_sso_email:
            continue

        service_now_user_id: str = ""
        try:
            service_now_user = service_now_interface.get_user(
                email=staff_sso_email.service_now_email_address,
            )
        except ServiceNowUserNotFound:
            continue
        else:
            service_now_user_id = service_now_user["sys_id"]

        # Get Service Now Department data
        service_now_department_id: str = settings.SERVICE_NOW_DIT_DEPARTMENT_SYS_ID
        service_now_department_name: str = ""
        service_now_departments = service_now_interface.get_departments(
            sys_id=service_now_department_id,
        )
        if len(service_now_departments) == 1:
            service_now_department_name = service_now_departments[0]["name"]

        staff_document_dict = staff_document.to_dict()
        staff_document_dict.update(
            service_now_user_id=service_now_user_id,
            service_now_department_id=service_now_department_id,
            service_now_department_name=service_now_department_name,
        )
        index_staff_document(
            staff_document=StaffDocument.from_dict(staff_document_dict),
        )
