from typing import List

from django.core.management.base import BaseCommand

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

        # Add documents to the index
        # TODO: populate list from integrations
        staff_documents: List[StaffDocument] = [
            {
                "staff_number": "123",
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@example.com",  # /PS-IGNORE
            },
        ]
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
