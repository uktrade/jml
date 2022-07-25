from django.core.management.base import BaseCommand

from core.utils.staff_index import (
    StaffIndexNotFound,
    create_staff_index,
    staff_index_mapping_changed,
)


class Command(BaseCommand):
    help = "Initialise the Staff Index if it doesn't exist"

    def handle(self, *args, **options):
        created = False
        try:
            staff_index_mapping_changed()
        except StaffIndexNotFound:
            create_staff_index()
            created = True

        if created:
            self.stdout.write(self.style.SUCCESS(("Staff index initialised")))
        else:
            self.stdout.write(self.style.SUCCESS(("Staff index already initialised")))
