from datetime import datetime

from django.test import TestCase
from django.utils.timezone import make_aware
from freezegun import freeze_time

from leavers.factories import LeavingRequestFactory
from leavers.workflow.tasks import EmailIds, ReminderEmail
from leavers.workflow.tests.factories import FlowFactory, TaskRecordFactory
from user.test.factories import UserFactory


class TestReminderEmail(TestCase):
    def setUp(self):
        self.user = UserFactory()

        self.flow = FlowFactory(executed_by=self.user)
        self.task_record = TaskRecordFactory(executed_by=self.user, flow=self.flow)
        self.leaving_request = LeavingRequestFactory(
            last_day=make_aware(datetime(2021, 12, 25)),
        )
        self.flow.leaving_request = self.leaving_request
        self.flow.save()

        self.task = ReminderEmail(self.user, self.task_record, self.flow)

        self.task_name = (
            "Some task name that contains an Email ID "
            f"{EmailIds.LEAVER_ROSA_REMINDER.value}"
        )
        self.task_info = {
            "email_id": EmailIds.LEAVER_ROSA_REMINDER.value,
        }

    @freeze_time("2021-12-5")
    def test_before_two_weeks(self):
        # Test no email sent yet
        self.assertFalse(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

    @freeze_time("2021-12-11")
    def test_exactly_two_weeks(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

    @freeze_time("2021-12-15")
    def test_before_one_week(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test 2 week email sent
        with freeze_time("2021-12-15"):
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=self.task_name,
            )
        self.assertFalse(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

    @freeze_time("2021-12-18")
    def test_exactly_one_week(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test 2 week email sent
        with freeze_time("2021-12-15"):
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=self.task_name,
            )
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

    @freeze_time("2021-12-19")
    def test_six_days(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test 1 week email sent
        with freeze_time("2021-12-18"):
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=self.task_name,
            )
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

    @freeze_time("2021-12-20")
    def test_five_days(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test 6 days email sent
        with freeze_time("2021-12-19"):
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=self.task_name,
            )
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

    @freeze_time("2021-12-21")
    def test_four_days(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test 5 days email sent
        with freeze_time("2021-12-20"):
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=self.task_name,
            )
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

    @freeze_time("2021-12-22")
    def test_three_days(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test 4 days email sent
        with freeze_time("2021-12-21"):
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=self.task_name,
            )
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

    @freeze_time("2021-12-23")
    def test_two_days(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test 3 days email sent
        with freeze_time("2021-12-22"):
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=self.task_name,
            )
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

    @freeze_time("2021-12-24")
    def test_one_day(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test 2 days email sent
        with freeze_time("2021-12-23"):
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=self.task_name,
            )
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

    @freeze_time("2021-12-25")
    def test_same_day(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test 1 days email sent
        with freeze_time("2021-12-24"):
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=self.task_name,
            )
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

    @freeze_time("2021-12-26")
    def test_one_day_after(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test same day email sent
        with freeze_time("2021-12-25"):
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=self.task_name,
            )
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

    @freeze_time("2021-12-27")
    def test_two_days_after(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test next day email sent
        with freeze_time("2021-12-26"):
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=self.task_name,
            )
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

    @freeze_time("2021-12-28")
    def test_three_days_after(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test 2 days after email sent
        with freeze_time("2021-12-27"):
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=self.task_name,
            )
        self.assertTrue(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                task_info=self.task_info,
                email_id=EmailIds.LEAVER_ROSA_REMINDER,
            )
        )
