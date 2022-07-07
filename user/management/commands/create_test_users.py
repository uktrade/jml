import uuid
from typing import List, Tuple

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from activity_stream.models import ActivityStreamStaffSSOUser
from user.models import User

# first name, last name, team /PS-IGNORE
USERS: List[Tuple[str, str, str]] = [
    ("John", "Smith", "Hardware Team"),  # /PS-IGNORE
    ("Jane", "Doe", "SRE"),  # /PS-IGNORE
    ("Miss", "Marple", "HR"),  # /PS-IGNORE
    ("Thomas", "Anderson", "Security Team"),  # /PS-IGNORE
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
        username = f"{first_name.lower()}.{last_name.lower()}@example.com"  # /PS-IGNORE

        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            group = Group.objects.create(
                name=group_name,
            )

        try:
            user = User.objects.get(username=username)

            self.stdout.write(f"{username} already exists")
            self.exists += 1
        except User.DoesNotExist:
            user = User.objects.create_user(
                username,
                email=username,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,
                is_superuser=True,
            )
            user.sso_legacy_user_id = str(uuid.uuid4())
            user.set_password("password")
            user.save()
            self.stdout.write(f"{username} created")
            self.created += 1

        group.user_set.add(user)
        self.stdout.write(f"{username} added to {group.name}")

        # Create ActivityStreamStaffSSOUser for each user
        _, created = ActivityStreamStaffSSOUser.objects.get_or_create(
            email_address=username,
            defaults={
                "identifier": uuid.uuid4(),
                "available": True,
                "name": f"{first_name} {last_name}",
                "obj_type": "dit:StaffSSO:User",
                "first_name": first_name,
                "last_name": last_name,
                "user_id": user.sso_legacy_user_id,
                "status": "active",
                "last_accessed": timezone.now(),
                "joined": timezone.now(),
                "email_user_id": "",
                "contact_email_address": "",
                "became_inactive_on": None,
            },
        )
        if created:
            self.stdout.write(f"ActivityStreamStaffSSOUser created for {username}")

        return user
