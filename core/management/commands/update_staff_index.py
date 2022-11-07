from django.core.management.base import BaseCommand

from core.utils.staff_index import (
    StaffIndexNotFound,
    clear_staff_index,
    create_staff_index,
    delete_staff_index,
    staff_index_mapping_changed,
)


class Command(BaseCommand):
    help = "Create/Update Staff ES Index"

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
                clear_staff_index()
                self.stdout.write(self.style.WARNING("Staff index cleared"))

        self.stdout.write(self.style.SUCCESS("Job finished successfully"))
