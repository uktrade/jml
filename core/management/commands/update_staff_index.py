from typing import Dict, List, Optional, Union

from django.conf import settings
from django.core.management.base import BaseCommand

from activity_stream.models import ActivityStreamStaffSSOUser
from core.people_finder import get_people_finder_interface
from core.people_finder.interfaces import PersonDetail
from core.service_now import get_service_now_interface
from core.utils.staff_index import (
    StaffDocument,
    StaffIndexNotFound,
    clear_staff_index,
    create_staff_index,
    delete_staff_index,
    index_staff_document,
    staff_index_mapping_changed,
)


class Command(BaseCommand):
    help = "Create/Update Staff ES Index"  # /PS-IGNORE

    def handle(self, *args, **options):
        try:
            mapping_has_changed = staff_index_mapping_changed()
        except StaffIndexNotFound:
            create_staff_index()
        else:
            if mapping_has_changed:
                # If the mapping has changed, delete and recreate the index
                self.stdout.write(self.style.WARNING("Staff index mapping has changed"))
                delete_staff_index()
                self.stdout.write(self.style.WARNING("Staff index deleted"))
                create_staff_index()
                self.stdout.write(self.style.WARNING("Staff index created"))
            else:
                # If the mapping hasn't changed, clear the index
                clear_staff_index()  # /PS-IGNORE
                self.stdout.write(self.style.WARNING("Staff index cleared"))

        indexed_count = self.index_staff()

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Job finished successfully\n"
                    f"{indexed_count} staff successfully indexed\n"
                )
            )
        )

    def index_staff(self) -> int:
        """
        Index all staff to the Staff Search Index

        POTENTIALLY LONG RUNNING TASK

        Things to consider:
        - API rate limits/throttling?
        - Using asyncronous tasks
        """
        people_finder_search = get_people_finder_interface()
        service_now_interface = get_service_now_interface()
        staff_documents: List[StaffDocument] = []
        # Add documents to the index
        for staff_sso_user in ActivityStreamStaffSSOUser.objects.all():
            # Get People Finder data
            people_finder_results = people_finder_search.get_search_results(
                search_term=staff_sso_user.email_address,
            )
            people_finder_result: Union[Dict, PersonDetail] = {}
            if len(people_finder_results) > 0:
                for pf_result in people_finder_results:
                    if pf_result["email"] == staff_sso_user.email_address:
                        people_finder_result = pf_result
            people_finder_directorate: Optional[str] = people_finder_result.get(
                "directorate"
            )

            # Get Service Now data
            service_now_department_id: str = settings.SERVICE_NOW_DIT_DEPARTMENT_SYS_ID
            service_now_department_name: str = ""
            service_now_departments = service_now_interface.get_departments(
                sys_id=service_now_department_id,
            )
            if len(service_now_departments) == 1:
                service_now_department_name = service_now_departments[0]["name"]
            service_now_directorate_id: str = ""
            service_now_directorate_name: str = ""
            if people_finder_directorate:
                service_now_directorates = service_now_interface.get_directorates(
                    name=people_finder_directorate,
                )
                if len(service_now_directorates) == 1:
                    service_now_directorate_id = service_now_directorates[0]["sys_id"]
                    service_now_directorate_name = service_now_directorates[0]["name"]

            staff_document: StaffDocument = {
                # Staff SSO
                "staff_sso_activity_stream_id": staff_sso_user.identifier,
                "staff_sso_first_name": staff_sso_user.first_name,
                "staff_sso_last_name": staff_sso_user.last_name,
                "staff_sso_email_address": staff_sso_user.email_address,
                "staff_sso_contact_email_address": staff_sso_user.contact_email_address,
                # People Finder
                "people_finder_image": people_finder_result.get("image", ""),
                "people_finder_first_name": people_finder_result.get("first_name"),
                "people_finder_last_name": people_finder_result.get("last_name"),
                "people_finder_job_title": people_finder_result.get("job_title"),
                "people_finder_directorate": people_finder_result.get("directorate"),
                "people_finder_phone": people_finder_result.get("phone"),
                "people_finder_grade": people_finder_result.get("grade"),
                # Service Now
                "service_now_department_id": service_now_department_id,
                "service_now_department_name": service_now_department_name,
                "service_now_directorate_id": service_now_directorate_id,
                "service_now_directorate_name": service_now_directorate_name,
            }

            # Add to list of Staff Documents
            staff_documents.append(staff_document)
        indexed_count = 0
        for staff_document in staff_documents:
            index_staff_document(staff_document=staff_document)
            indexed_count += 1

        return indexed_count
