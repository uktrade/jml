from django.test import TestCase

from core.utils.sre_messages import (
    FailedToSendSREReminderMessage,
    send_sre_reminder_message,
)
from leavers.factories import LeavingRequestFactory, SlackMessageFactory
from leavers.workflow.tasks import EmailIds


class TestSendSREReminderMessage(TestCase):
    def setUp(self) -> None:
        self.leaving_request = LeavingRequestFactory()

    def test_wrong_email_id(self):
        response = send_sre_reminder_message(
            email_id=EmailIds.LEAVER_THANK_YOU_EMAIL,
            leaving_request=self.leaving_request,
        )
        self.assertIsNone(response)
        self.assertEqual(self.leaving_request.slack_messages.count(), 0)

    def test_no_slack_message_found(self):
        with self.assertRaises(FailedToSendSREReminderMessage):
            send_sre_reminder_message(
                email_id=EmailIds.SRE_REMINDER_DAY_AFTER_LWD,
                leaving_request=self.leaving_request,
            )
        self.assertEqual(self.leaving_request.slack_messages.count(), 0)

    def test_success(self):
        SlackMessageFactory(leaving_request=self.leaving_request)
        self.assertEqual(self.leaving_request.slack_messages.count(), 1)

        response = send_sre_reminder_message(
            email_id=EmailIds.SRE_REMINDER_DAY_AFTER_LWD,
            leaving_request=self.leaving_request,
        )
        self.assertIsNotNone(response)
        self.leaving_request.refresh_from_db()
        self.assertEqual(self.leaving_request.slack_messages.count(), 2)

        response = send_sre_reminder_message(
            email_id=EmailIds.SRE_REMINDER_ONE_DAY_AFTER_LD,
            leaving_request=self.leaving_request,
        )
        self.assertIsNotNone(response)
        self.assertEqual(self.leaving_request.slack_messages.count(), 3)

        response = send_sre_reminder_message(
            email_id=EmailIds.SRE_REMINDER_TWO_DAYS_AFTER_LD_PROC,
            leaving_request=self.leaving_request,
        )
        self.assertIsNotNone(response)
        self.assertEqual(self.leaving_request.slack_messages.count(), 4)
