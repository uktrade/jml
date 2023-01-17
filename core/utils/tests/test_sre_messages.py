from unittest import mock

from django.test import TestCase
from django.utils import timezone

from core.utils.sre_messages import send_sre_reminder_message
from leavers.factories import LeavingRequestFactory, SlackMessageFactory
from leavers.workflow.tasks import EmailIds


class MockSlackResponse:
    data = {
        "ts": timezone.now().isoformat(),
    }


@mock.patch(
    "core.utils.sre_messages.send_slack_message",
    return_value=MockSlackResponse(),
)
class TestSendSREReminderMessage(TestCase):
    def setUp(self) -> None:
        self.leaving_request = LeavingRequestFactory()

    def test_wrong_email_id(self, mock_send_slack_message: mock.Mock):
        response = send_sre_reminder_message(
            email_id=EmailIds.LEAVER_THANK_YOU_EMAIL,
            leaving_request=self.leaving_request,
        )
        self.assertIsNone(response)
        self.assertEqual(self.leaving_request.slack_messages.count(), 0)
        mock_send_slack_message.assert_not_called()

    def test_success(self, mock_send_slack_message: mock.Mock):
        SlackMessageFactory(leaving_request=self.leaving_request)
        self.assertEqual(self.leaving_request.slack_messages.count(), 1)

        response = send_sre_reminder_message(
            email_id=EmailIds.SRE_REMINDER_DAY_AFTER_LWD,
            leaving_request=self.leaving_request,
        )
        self.assertIsNotNone(response)
        self.leaving_request.refresh_from_db()
        self.assertEqual(self.leaving_request.slack_messages.count(), 2)

        self.assertEqual(mock_send_slack_message.call_count, 1)

        response = send_sre_reminder_message(
            email_id=EmailIds.SRE_REMINDER_ONE_DAY_AFTER_LD,
            leaving_request=self.leaving_request,
        )
        self.assertIsNotNone(response)
        self.assertEqual(self.leaving_request.slack_messages.count(), 3)

        self.assertEqual(mock_send_slack_message.call_count, 2)

        response = send_sre_reminder_message(
            email_id=EmailIds.SRE_REMINDER_TWO_DAYS_AFTER_LD_PROC,
            leaving_request=self.leaving_request,
        )
        self.assertIsNotNone(response)
        self.assertEqual(self.leaving_request.slack_messages.count(), 4)

        self.assertEqual(mock_send_slack_message.call_count, 3)
