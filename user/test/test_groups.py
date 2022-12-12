from django.contrib.auth.models import Group
from django.core.management import call_command

EXPECTED_GROUP_COUNT = 3


def test_group_count(db):
    assert Group.objects.count() == EXPECTED_GROUP_COUNT


def test_create_groups_command(db):
    assert Group.objects.count() == EXPECTED_GROUP_COUNT
    call_command("create_groups")
    assert Group.objects.count() == EXPECTED_GROUP_COUNT
