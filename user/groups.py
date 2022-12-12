from enum import Enum

from django.contrib.auth.models import Group


class GroupName(Enum):
    SECURITY_TEAM = "Security Team"
    SRE = "SRE"
    HR = "HR"


def get_group(group_name: GroupName) -> Group:
    return Group.objects.get(name=group_name.value)
