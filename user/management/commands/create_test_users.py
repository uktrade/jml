from typing import List, Tuple

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from user.models import User

# first name, last name
USERS: List[Tuple[str, str]] = [
    ("John", "Smith", "Hardware Team"),
    # ("Jane", "Doe"),
    # ("Elon", "Musk"),
    # ("Bill", "Gates"),
    # ("Ada", "Lovelace"),
    # ("Grace", "Hopper"),
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
        username = f"{first_name.lower()}.{last_name.lower()}@example.com"

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
            user.set_password("password")
            user.save()
            self.stdout.write(f"{username} created")
            self.created += 1

        group.user_set.add(user)
        self.stdout.write(f"{username} added to {group.name}")

        return user
