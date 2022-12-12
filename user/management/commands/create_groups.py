from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from user.groups import GroupName


class Command(BaseCommand):
    help = "Create and manage all the groups for the application"

    def handle(self, *args, **options):
        security_team, security_team_created = Group.objects.get_or_create(
            name=GroupName.SECURITY_TEAM.value
        )
        sre, sre_created = Group.objects.get_or_create(name=GroupName.SRE.value)
        hr, hr_created = Group.objects.get_or_create(name=GroupName.HR.value)

        hr.permissions.set(
            Permission.objects.filter(
                codename__in=[
                    "select_leaver",
                ],
                content_type__app_label="leavers",
            )
        )

        groups_created = [
            security_team_created,
            sre_created,
            hr_created,
        ]

        self.stdout.write(
            self.style.SUCCESS(f"Success! {groups_created.count(True)} groups created")
        )
