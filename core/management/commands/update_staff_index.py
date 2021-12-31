from typing import List

from django.core.management.base import BaseCommand

from activity_stream.models import ActivityStreamStaffSSOUser
from core.utils.es_staff_index import (
    StaffDocument,
    clear_staff_index,
    create_staff_index,
    delete_staff_index,
    index_staff_document,
    staff_index_mapping_changed,
)


class Command(BaseCommand):
    help = "Create/Update Staff ES Index"  # /PS-IGNORE

    def handle(self, *args, **options):
        if staff_index_mapping_changed():
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

        """
        START OF POTENTIALLY LONG RUNNING TASK

        Things to consider:
        - API rate limits/throttling?
        - Using asyncronous tasks
        """

        staff_documents: List[StaffDocument] = []
        # Add documents to the index
        for staff_sso_user in ActivityStreamStaffSSOUser.objects.all():
            # TODO: populate list from integrations
            staff_document: StaffDocument = {
                "staff_sso_activity_stream_id": staff_sso_user.identifier,
                "staff_sso_first_name": staff_sso_user.first_name,
                "staff_sso_last_name": staff_sso_user.last_name,
                "staff_sso_email_address": staff_sso_user.email_address,
                "staff_sso_contact_email_address": staff_sso_user.contact_email_address,
            }
            staff_documents.append(staff_document)
        indexed_count = 0
        for staff_document in staff_documents:
            index_staff_document(staff_document=staff_document)
            indexed_count += 1

        """
        END OF POTENTIALLY LONG RUNNING TASK
        """

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Job finished successfully\n"
                    f"{indexed_count} staff successfully indexed\n"
                )
            )
        )
