from datetime import datetime
from unittest import mock

from django.test import TestCase
from django.utils.timezone import make_aware
from freezegun import freeze_time

from leavers.factories import LeavingRequestFactory
from leavers.workflow.tasks import EmailIds, ProcessorReminderEmail, ReminderEmail
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
            f"{EmailIds.LINE_MANAGER_CORRECTION.value}"
        )

    @freeze_time("2021-12-5")
    def test_before_two_weeks(self):
        # Test no email sent yet
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

    @freeze_time("2021-12-11")
    def test_exactly_two_weeks(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

    @freeze_time("2021-12-15")
    def test_before_one_week(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
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
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

    @freeze_time("2021-12-18")
    def test_exactly_one_week(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
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
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

    @freeze_time("2021-12-19")
    def test_six_days(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
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
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

    @freeze_time("2021-12-20")
    def test_five_days(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
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
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

    @freeze_time("2021-12-21")
    def test_four_days(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
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
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

    @freeze_time("2021-12-22")
    def test_three_days(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
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
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

    @freeze_time("2021-12-23")
    def test_two_days(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
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
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

    @freeze_time("2021-12-24")
    def test_one_day(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
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
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

    @freeze_time("2021-12-25")
    def test_same_day(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
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
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

    @freeze_time("2021-12-26")
    def test_one_day_after(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
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
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

    @freeze_time("2021-12-27")
    def test_two_days_after(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
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
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

    @freeze_time("2021-12-28")
    def test_three_days_after(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
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
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test email already sent
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )


class TestProcessorReminderEmail(TestCase):
    def setUp(self):
        self.user = UserFactory()

        self.flow = FlowFactory(executed_by=self.user)
        self.task_record = TaskRecordFactory(executed_by=self.user, flow=self.flow)
        self.leaving_request = LeavingRequestFactory(
            last_day=make_aware(datetime(2021, 12, 25)),
            leaving_date=make_aware(datetime(2021, 12, 30)),
        )
        self.flow.leaving_request = self.leaving_request
        self.flow.save()

        self.task = ProcessorReminderEmail(self.user, self.task_record, self.flow)
        self.task_info = {"processor_email": "someone@example.com"}  # /PS-IGNORE
        self.email_ids = {
            "day_after_lwd": EmailIds.SECURITY_OFFBOARD_BP_REMINDER_DAY_AFTER_LWD,
            "two_days_after_lwd": EmailIds.SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LWD,
            "on_ld": EmailIds.SECURITY_OFFBOARD_BP_REMINDER_ONE_DAY_AFTER_LD,
            "one_day_after_ld": EmailIds.SECURITY_OFFBOARD_BP_REMINDER_ONE_DAY_AFTER_LD,
            "two_days_after_ld_lm": EmailIds.SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_LM,
            "two_days_after_ld_proc": EmailIds.SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_PROC,
        }
        self.task_info.update(**self.email_ids)

    @freeze_time("2021-12-30")
    def test_should_send_email_none_sent_late(self):
        for _, email_id in self.email_ids.items():
            with self.subTest(email_id=email_id):
                self.assertTrue(self.task.should_send_email(email_id=email_id))

    @freeze_time("2021-12-30")
    def test_should_send_email_already_sent(self):
        for _, email_id in self.email_ids.items():
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=f"Some task name that contains an Email ID {email_id.value}",
            )
            with self.subTest(email_id=email_id):
                self.assertFalse(self.task.should_send_email(email_id=email_id))

    @freeze_time("2021-12-5")
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_early(self, mock_get_send_email_method):
        self.task.execute(task_info=self.task_info)
        mock_get_send_email_method.assert_not_called()

    @freeze_time("2021-12-26")
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_day_after_lwd(self, mock_get_send_email_method):
        self.task.execute(task_info=self.task_info)
        mock_get_send_email_method.assert_called_once_with(
            email_id=self.email_ids["day_after_lwd"]
        )

    @freeze_time("2021-12-27")
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_two_days_after_lwd(self, mock_get_send_email_method):
        for _, email_id in self.email_ids.items():
            if email_id != self.email_ids["two_days_after_lwd"]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id.value}",
                )

        self.task.execute(task_info=self.task_info)
        mock_get_send_email_method.assert_called_once_with(
            email_id=self.email_ids["two_days_after_lwd"]
        )

    @freeze_time("2021-12-31")
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_on_ld(self, mock_get_send_email_method):
        for _, email_id in self.email_ids.items():
            if email_id != self.email_ids["on_ld"]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id.value}",
                )

        self.task.execute(task_info=self.task_info)
        mock_get_send_email_method.assert_called_once_with(
            email_id=self.email_ids["on_ld"]
        )

    @freeze_time("2022-1-1")
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_one_day_after_ld(self, mock_get_send_email_method):
        for _, email_id in self.email_ids.items():
            if email_id != self.email_ids["one_day_after_ld"]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id.value}",
                )

        self.task.execute(task_info=self.task_info)
        mock_get_send_email_method.assert_called_once_with(
            email_id=self.email_ids["one_day_after_ld"]
        )

    @freeze_time("2022-1-1")
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_two_days_after_ld(self, mock_get_send_email_method):
        for _, email_id in self.email_ids.items():
            if email_id not in [
                self.email_ids["two_days_after_ld_lm"],
                self.email_ids["two_days_after_ld_proc"],
            ]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id.value}",
                )

        self.task.execute(task_info=self.task_info)
        calls = mock_get_send_email_method.call_args_list

        self.assertEqual(
            calls[0].kwargs["email_id"], self.email_ids["two_days_after_ld_lm"]
        )
        self.assertEqual(
            calls[1].kwargs["email_id"], self.email_ids["two_days_after_ld_proc"]
        )
