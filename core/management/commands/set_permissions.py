"""
Command to make sure that all groups have the correct permissions.
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

GROUP_PERMISSION_MAPPING = {"HR": ["leavers.select_leaver"]}


class Command(BaseCommand):
    help = "Set permissions to groups."

    def handle(self, *args, **options) -> None:
        for group in Group.objects.all():
            if group.name in GROUP_PERMISSION_MAPPING:
                permissions = GROUP_PERMISSION_MAPPING[group.name]
                for permission in permissions:
                    app_label, codename = permission.split(".")
                    permission_obj = Permission.objects.get(
                        content_type__app_label=app_label, codename=codename
                    )
                    group.permissions.add(permission_obj)
