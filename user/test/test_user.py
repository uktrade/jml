import uuid

from django.test import TestCase

from user.backends import CustomAuthbrokerBackend
from user.groups import GroupName, get_group
from user.models import User
from user.test.factories import UserFactory


class TestSSOUserProfile(TestCase):
    def setUp(self):
        self.sso_profile = {
            "email_user_id": "sso_test-1111111@example.com",  # /PS-IGNORE
            "email": "sso.test@example.com",  # /PS-IGNORE
            "contact_email": "sso_test_1@example.com",  # /PS-IGNORE
            "first_name": "Barry",  # /PS-IGNORE
            "last_name": "Test",
            "user_id": str(uuid.uuid4()),
        }

    def test_new_user_created(self):
        user_count = User.objects.count()

        CustomAuthbrokerBackend.get_or_create_user(
            self.sso_profile,
        )

        self.assertEqual(User.objects.count(), user_count + 1)

        user = User.objects.get(email="sso.test@example.com")  # /PS-IGNORE

        self.assertEqual(
            user.username,
            self.sso_profile["email_user_id"],
        )
        self.assertEqual(
            user.email,
            self.sso_profile["email"],
        )
        self.assertEqual(
            user.first_name,
            self.sso_profile["first_name"],
        )
        self.assertEqual(
            user.last_name,
            self.sso_profile["last_name"],
        )
        self.assertEqual(
            user.sso_legacy_user_id,
            self.sso_profile["user_id"],
        )


def test_is_in_group(db):
    group_name = GroupName.HR
    group = get_group(group_name)

    user = UserFactory()
    user.groups.add(group)

    assert user.is_in_group(group_name) is True
