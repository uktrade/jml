from typing import List, Tuple

from dev_tools import utils as dev_tools_utils
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from core.utils.staff_index import build_staff_document, update_staff_document
from user.models import User

# first name, last name, team /PS-IGNORE
USERS: List[Tuple[str, str, str]] = [
    ("John", "Smith", "Hardware Team"),  # /PS-IGNORE
    ("Jane", "Doe", "SRE"),  # /PS-IGNORE
    ("Miss", "Marple", "HR"),  # /PS-IGNORE
    ("Thomas", "Anderson", "Security Team"),  # /PS-IGNORE
    ("Charlotte", "Blackwood", "Asset Team"),  # /PS-IGNORE
]


class Command(BaseCommand):
    help = "Create users for local testing purposes"

    def handle(self, *args, **options):
        self.exists = 0
        self.created = 0

        for first_name, last_name, group in USERS:
            self.create_user(first_name, last_name, group)

        self.stdout.write(
            self.style.SUCCESS(
                "Job finished successfully\n"
                f"{self.exists} users already existed\n"
                f"{self.created} users created"
            )
        )

    def create_user(self, first_name: str, last_name: str, group_name: str) -> User:
        email = f"{first_name.lower()}.{last_name.lower()}@example.com"  # /PS-IGNORE

        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            group = Group.objects.create(
                name=group_name,
            )

        user, created, staff_sso_user = dev_tools_utils.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            group=group,
        )

        if not created:
            self.stdout.write(f"User {email} already exists")
            self.exists += 1
        else:
            self.stdout.write(f"User for '{email}' created")
            self.created += 1

        # Index the user into the staff index
        staff_document = build_staff_document(staff_sso_user=staff_sso_user)
        update_staff_document(
            staff_document.staff_sso_email_user_id,
            staff_document=staff_document.to_dict(),
            upsert=True,
        )

        return user
