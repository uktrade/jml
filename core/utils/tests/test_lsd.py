from unittest import mock

from django.test import TestCase
from django.utils import timezone

import core.utils.lsd as lsd
from activity_stream.factories import ActivityStreamStaffSSOUserFactory
from core.utils.tests.mock_zenpy import (
    MockZenpyAPI,
    MockZenpyUser,
    MockZenpyUserResponse,
)
from leavers.factories import LeavingRequestFactory
from user.test.factories import UserFactory

mock_user = MockZenpyUser(
    id=1234,
    name="Jim Example",  # /PS-IGNORE
    email="test@example.com",  # /PS-IGNORE
)


@mock.patch(
    "core.utils.lsd.Zenpy",  # /PS-IGNORE
    return_value=MockZenpyAPI(users=[mock_user], me=MockZenpyUserResponse(1234)),
)
class TestInformLSDTeamOfLeaver(TestCase):
    def setUp(self) -> None:
        leaver = UserFactory()
        manager = UserFactory()
        leaving_date = timezone.now()
        self.leaving_request = LeavingRequestFactory(
            leaver_complete=leaving_date,
            last_day=leaving_date,
            leaving_date=leaving_date,
            leaver_activitystream_user=ActivityStreamStaffSSOUserFactory(
                email_user_id=leaver.sso_email_user_id
            ),
            manager_activitystream_user=ActivityStreamStaffSSOUserFactory(
                email_user_id=manager.sso_email_user_id
            ),
        )

    def test_no_leaving_date(self, mock_zenpy_client: mock.Mock):
        self.leaving_request.leaving_date = None

        with self.assertRaises(Exception):
            lsd.inform_lsd_team_of_leaver(leaving_request=self.leaving_request)
            self.assertEqual(mock_zenpy_client.call_count, 0)

    def test_success(self, mock_zenpy_client: mock.Mock):

        lsd.inform_lsd_team_of_leaver(
            leaving_request=self.leaving_request,
        )

        self.assertEqual(mock_zenpy_client.call_count, 1)
