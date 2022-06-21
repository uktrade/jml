from django.conf import settings

from core.service_now import get_service_now_interface
from core.service_now.interfaces import ServiceNowUserNotFound
from core.utils.staff_index import (
    StaffDocument,
    get_all_staff_documents,
    index_staff_document,
)


def ingest_service_now():
    service_now_interface = get_service_now_interface()

    for staff_document in get_all_staff_documents():
        service_now_user_id: str = ""
        try:
            service_now_user = service_now_interface.get_user(
                email=staff_document.staff_sso_email_address,
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

        people_finder_directorate: str = staff_document.people_finder_directorate

        # Get Service Now Directorate data
        service_now_directorate_id: str = ""
        service_now_directorate_name: str = ""
        if people_finder_directorate:
            service_now_directorates = service_now_interface.get_directorates(
                name=people_finder_directorate,
            )
            if len(service_now_directorates) == 1:
                service_now_directorate_id = service_now_directorates[0]["sys_id"]
                service_now_directorate_name = service_now_directorates[0]["name"]

        staff_document_dict = staff_document.to_dict()
        staff_document_dict.update(
            service_now_user_id=service_now_user_id,
            service_now_department_id=service_now_department_id,
            service_now_department_name=service_now_department_name,
            service_now_directorate_id=service_now_directorate_id,
            service_now_directorate_name=service_now_directorate_name,
        )
        index_staff_document(
            staff_document=StaffDocument.from_dict(staff_document_dict),
        )
