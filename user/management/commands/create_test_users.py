from typing import List, Optional, Tuple

from dev_tools import utils as dev_tools_utils
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from user.models import User

# first name, last name, team /PS-IGNORE
USERS: List[Tuple[str, str, str, Optional[str]]] = [
    ("John", "Smith", "Hardware Team", None),  # /PS-IGNORE
    ("Jane", "Doe", "SRE", None),  # /PS-IGNORE
    ("Miss", "Marple", "HR", None),  # /PS-IGNORE
    ("Thomas", "Anderson", "Security Team", None),  # /PS-IGNORE
    ("Charlotte", "Blackwood", "Asset Team", None),  # /PS-IGNORE
    ("John", "Watson", "Hardware Team", "digital.trade.gov.uk"),  # /PS-IGNORE
]


class Command(BaseCommand):
    help = "Create users for local testing purposes"

    def handle(self, *args, **options):
        self.exists = 0
        self.created = 0

        for first_name, last_name, group, email_domain in USERS:
            self.create_user(first_name, last_name, group, email_domain)

        self.stdout.write(
            self.style.SUCCESS(
                "Job finished successfully\n"
                f"{self.exists} users already existed\n"
                f"{self.created} users created"
            )
        )

    def create_user(
        self,
        first_name: str,
        last_name: str,
        group_name: str,
        email_domain: Optional[str],
    ) -> User:
        if not email_domain:
            email_domain = "example.com"

        email = f"{first_name.lower()}.{last_name.lower()}@{email_domain}"  # /PS-IGNORE

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

        return user
