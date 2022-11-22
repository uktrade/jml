from datetime import datetime
from typing import List
from unittest import mock

from django.test import TestCase
from django.utils.timezone import make_aware
from freezegun import freeze_time

from leavers.factories import (
    LeaverInformationFactory,
    LeavingRequestFactory,
    TaskLogFactory,
)
from leavers.models import LeaverInformation, LeavingRequest
from leavers.types import ReminderEmailDict
from leavers.workflow.tasks import (
    SECURITY_TEAM_BP_REMINDER_EMAILS,
    SRE_REMINDER_EMAILS,
    DailyReminderEmail,
    EmailIds,
    ProcessorReminderEmail,
    ReminderEmail,
    SkipCondition,
    UKSBSSendLeaverDetails,
)
from leavers.workflow.tests.factories import FlowFactory, TaskRecordFactory
from user.test.factories import UserFactory


class TestSkipConditions(TestCase):
    def setUp(self):
        self.user = UserFactory()

        self.flow = FlowFactory(executed_by=self.user)
        self.task_record = TaskRecordFactory(executed_by=self.user, flow=self.flow)
        self.leaving_request: LeavingRequest = LeavingRequestFactory(
            last_day=make_aware(datetime(2021, 12, 25)),
        )
        self.leaver_information: LeaverInformation = LeaverInformationFactory(
            leaving_request=self.leaving_request
        )
        self.flow.leaving_request = self.leaving_request
        self.flow.save()

        self.task = ReminderEmail(
            self.user,
            self.task_record,
            self.flow,
        )
        self.uk_sbs_task = UKSBSSendLeaverDetails(
            self.user,
            self.task_record,
            self.flow,
        )

    def test_no_skip_condition(self):
        self.assertFalse(
            self.task.should_skip(
                task_info={},
            )
        )

    def test_rosa_skip(self):
        self.leaving_request.is_rosa_user = True
        self.leaving_request.save()
        self.assertFalse(
            self.task.should_skip(
                task_info={"skip_condition": SkipCondition.IS_NOT_ROSA_USER.value},
            )
        )
        self.leaving_request.is_rosa_user = False
        self.leaving_request.save()
        self.assertTrue(
            self.task.should_skip(
                task_info={"skip_condition": SkipCondition.IS_NOT_ROSA_USER.value},
            )
        )

    def test_manually_offboarded_from_uksbs_skip(self):
        self.assertFalse(
            self.uk_sbs_task.should_skip(
                task_info={
                    "skip_condition": SkipCondition.MANUALLY_OFFBOARDED_FROM_UKSBS.value
                },
            )
        )
        self.leaving_request.manually_offboarded_from_uksbs = TaskLogFactory()
        self.leaving_request.save()
        self.assertTrue(
            self.uk_sbs_task.should_skip(
                task_info={
                    "skip_condition": SkipCondition.MANUALLY_OFFBOARDED_FROM_UKSBS.value
                },
            )
        )


class TestDailyReminderEmail(TestCase):
    def setUp(self):
        self.user = UserFactory()

        self.flow = FlowFactory(executed_by=self.user)
        self.task_record = TaskRecordFactory(executed_by=self.user, flow=self.flow)
        self.leaving_request = LeavingRequestFactory(
            last_day=make_aware(datetime(2021, 12, 15)),
        )
        self.flow.leaving_request = self.leaving_request
        self.flow.save()

        self.task = DailyReminderEmail(self.user, self.task_record, self.flow)

        self.task_name = (
            "Some task name that contains an Email ID "
            f"{EmailIds.LINE_MANAGER_CORRECTION.value}"
        )

    @freeze_time("2021-11-30 12:00:00")  # Tuesday
    def test_daily_logic(self):
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )
        self.leaving_request.email_task_logs.create(
            user=self.user,
            task_name=self.task_name,
        )
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        with freeze_time("2022-12-2 12:00:00"):  # Wednesday
            self.assertTrue(
                self.task.should_send_email(
                    email_id=EmailIds.LINE_MANAGER_CORRECTION,
                )
            )
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=self.task_name,
            )
            self.assertFalse(
                self.task.should_send_email(
                    email_id=EmailIds.LINE_MANAGER_CORRECTION,
                )
            )

        with freeze_time("2022-12-3 12:00:00"):  # Thursday
            self.assertTrue(
                self.task.should_send_email(
                    email_id=EmailIds.LINE_MANAGER_CORRECTION,
                )
            )
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=self.task_name,
            )
            self.assertFalse(
                self.task.should_send_email(
                    email_id=EmailIds.LINE_MANAGER_CORRECTION,
                )
            )


class TestReminderEmail(TestCase):
    def setUp(self):
        self.user = UserFactory()

        self.flow = FlowFactory(executed_by=self.user)
        self.task_record = TaskRecordFactory(executed_by=self.user, flow=self.flow)
        self.leaving_request = LeavingRequestFactory(
            last_day=make_aware(datetime(2021, 12, 15)),
        )
        self.flow.leaving_request = self.leaving_request
        self.flow.save()

        self.task = ReminderEmail(self.user, self.task_record, self.flow)

        self.task_name = (
            "Some task name that contains an Email ID "
            f"{EmailIds.LINE_MANAGER_CORRECTION.value}"
        )

    @freeze_time("2021-11-30 12:00:00")  # Tuesday
    def test_before_two_weeks(self):
        # Test no email sent yet
        self.assertFalse(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

    @freeze_time("2022-12-1 12:00:00")  # Wednesday
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

    @freeze_time("2022-12-2 12:00:00")  # Friday
    def test_before_one_week(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test 2 week email sent
        with freeze_time("2022-12-7 12:00:00"):  # Wednesday
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

    @freeze_time("2022-12-9 12:00:00")  # Wednesday
    def test_exactly_one_week(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test 2 week email sent
        with freeze_time("2022-11-30 12:00:00"):  # Wednesday
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

    @freeze_time("2022-12-8 12:00:00")  # Thursday
    def test_six_days(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test 1 week email sent
        with freeze_time("2022-12-7 12:00:00"):  # Wednesday
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

    @freeze_time("2022-12-9 12:00:00")  # Friday
    def test_five_days(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test 6 days email sent
        with freeze_time("2022-12-8 12:00:00"):  # Thursday
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

    @freeze_time("2022-12-10 12:00:00")  # Saturday
    def test_four_days(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test 5 days email sent
        with freeze_time("2022-12-9 12:00:00"):
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

    @freeze_time("2022-12-11 12:00:00")  # Sunday
    def test_three_days(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test 4 days email sent
        with freeze_time("2022-12-10 12:00:00"):  # Saturday
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

    @freeze_time("2022-12-12 12:00:00")  # Monday
    def test_two_days(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test 3 days email sent
        with freeze_time("2022-12-11 12:00:00"):  # Sunday
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

    @freeze_time("2022-12-13 12:00:00")  # Tuesday
    def test_one_day(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test 2 days email sent
        with freeze_time("2022-12-12 12:00:00"):  # Monday
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

    @freeze_time("2022-12-14 12:00:00")  # Wednesday
    def test_same_day(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test 1 days email sent
        with freeze_time("2022-12-13 12:00:00"):  # Tuesday
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

    @freeze_time("2022-12-15 12:00:00")  # Thursday
    def test_one_day_after(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test same day email sent
        with freeze_time("2022-12-14 12:00:00"):  # Wednesday
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

    @freeze_time("2022-12-16 12:00:00")  # Friday
    def test_two_days_after(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test next day email sent
        with freeze_time("2022-12-15 12:00:00"):  # Thursday
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

    @freeze_time("2022-12-17 12:00:00")  # Saturday
    def test_three_days_after(self):
        # Test no email sent yet
        self.assertTrue(
            self.task.should_send_email(
                email_id=EmailIds.LINE_MANAGER_CORRECTION,
            )
        )

        # Test 2 days after email sent
        with freeze_time("2022-12-16 12:00:00"):  # Friday
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

        # Leaving Request with different dates
        self.flow = FlowFactory(executed_by=self.user)
        self.task_record = TaskRecordFactory(executed_by=self.user, flow=self.flow)
        self.leaving_request = LeavingRequestFactory(
            last_day=make_aware(datetime(2022, 12, 5)),  # Monday
            leaving_date=make_aware(datetime(2022, 12, 9)),  # Friday
        )
        self.flow.leaving_request = self.leaving_request
        self.flow.save()

        # Leaving Request with same dates
        self.flow2 = FlowFactory(executed_by=self.user)
        self.task_record2 = TaskRecordFactory(executed_by=self.user, flow=self.flow2)
        self.leaving_request2 = LeavingRequestFactory(
            last_day=make_aware(datetime(2022, 12, 9)),  # Friday
            leaving_date=make_aware(datetime(2022, 12, 9)),  # Friday
        )
        self.flow2.leaving_request = self.leaving_request2
        self.flow2.save()

        self.task = ProcessorReminderEmail(self.user, self.task_record, self.flow)
        self.task2 = ProcessorReminderEmail(self.user, self.task_record2, self.flow2)
        self.task_info = {"processor_emails": ["someone@example.com"]}  # /PS-IGNORE
        self.email_ids: ReminderEmailDict = SECURITY_TEAM_BP_REMINDER_EMAILS
        self.task_info.update(**self.email_ids)

    @freeze_time("2022-12-5 12:00:00")  # Monday
    def test_should_send_slack_none_sent_late(self):
        for _, email_id in self.email_ids.items():
            with self.subTest(email_id=email_id):
                self.assertTrue(
                    self.task.should_send_email(email_id=EmailIds(email_id))
                )

    @freeze_time("2022-12-5 12:00:00")  # Monday
    def test_should_send_email_already_sent(self):
        for _, email_id in self.email_ids.items():
            self.leaving_request.email_task_logs.create(
                user=self.user,
                task_name=f"Some task name that contains an Email ID {email_id}",
            )
            with self.subTest(email_id=email_id):
                self.assertFalse(
                    self.task.should_send_email(email_id=EmailIds(email_id))
                )

    @freeze_time("2022-12-5 12:00:00")  # Monday
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_early(self, mock_get_send_email_method):
        self.task.execute(task_info=self.task_info)
        mock_get_send_email_method.assert_not_called()

    @freeze_time("2022-12-6 12:00:00")  # Tuesday
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_day_after_lwd(self, mock_get_send_email_method):
        self.task.execute(task_info=self.task_info)
        mock_get_send_email_method.assert_called_once_with(
            email_id=EmailIds(self.email_ids["day_after_lwd"])
        )

    @freeze_time("2022-12-7 12:00:00")  # Wednesday
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_two_days_after_lwd(self, mock_get_send_email_method):
        for _, email_id in self.email_ids.items():
            if email_id != self.email_ids["two_days_after_lwd"]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id}",
                )

        self.task.execute(task_info=self.task_info)
        mock_get_send_email_method.assert_called_once_with(
            email_id=EmailIds(self.email_ids["two_days_after_lwd"])
        )

    @freeze_time("2022-12-16 12:00:00")  # Friday
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_on_ld(self, mock_get_send_email_method):
        for _, email_id in self.email_ids.items():
            if email_id != self.email_ids["on_ld"]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id}",
                )

        self.task.execute(task_info=self.task_info)
        mock_get_send_email_method.assert_called_once_with(
            email_id=EmailIds(self.email_ids["on_ld"])
        )

    @freeze_time("2022-12-10 12:00:00")  # Saturday
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_one_day_after_ld_weekend(self, mock_get_send_email_method):
        for _, email_id in self.email_ids.items():
            if email_id != self.email_ids["one_day_after_ld"]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id}",
                )

        self.task.execute(task_info=self.task_info)
        mock_get_send_email_method.assert_not_called()

    @freeze_time("2022-12-12 12:00:00")  # Monday
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_one_day_after_ld_weekday(self, mock_get_send_email_method):
        for _, email_id in self.email_ids.items():
            if email_id != self.email_ids["one_day_after_ld"]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id}",
                )

        self.task.execute(task_info=self.task_info)
        mock_get_send_email_method.assert_called_once_with(
            email_id=EmailIds(self.email_ids["one_day_after_ld"])
        )

    @freeze_time("2022-12-11 12:00:00")  # Sunday
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_two_days_after_ld_weekend(self, mock_get_send_email_method):
        for _, email_id in self.email_ids.items():
            if email_id not in [
                self.email_ids["two_days_after_ld_lm"],
                self.email_ids["two_days_after_ld_proc"],
            ]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id}",
                )

        self.task.execute(task_info=self.task_info)
        mock_get_send_email_method.assert_not_called()

    @freeze_time("2022-12-12 12:00:00")  # Monday
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_two_days_after_ld_weekday(self, mock_get_send_email_method):
        for _, email_id in self.email_ids.items():
            if email_id not in [
                self.email_ids["two_days_after_ld_lm"],
                self.email_ids["two_days_after_ld_proc"],
            ]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id}",
                )

        self.task.execute(task_info=self.task_info)
        calls = mock_get_send_email_method.call_args_list

        self.assertEqual(
            calls[0].kwargs["email_id"].value, self.email_ids["two_days_after_ld_lm"]
        )
        self.assertEqual(
            calls[1].kwargs["email_id"].value, self.email_ids["two_days_after_ld_proc"]
        )

    @freeze_time("2022-12-12 12:00:00")  # Monday
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_different_ld_and_lwd(self, mock_get_send_email_method):
        self.task.execute(task_info=self.task_info)
        calls = mock_get_send_email_method.call_args_list

        called_email_ids: List[str] = [call.kwargs["email_id"].value for call in calls]

        self.assertIn(self.email_ids["day_after_lwd"], called_email_ids)
        self.assertIn(self.email_ids["two_days_after_lwd"], called_email_ids)
        self.assertIn(self.email_ids["on_ld"], called_email_ids)
        self.assertIn(self.email_ids["one_day_after_ld"], called_email_ids)
        self.assertIn(self.email_ids["two_days_after_ld_lm"], called_email_ids)
        self.assertIn(self.email_ids["two_days_after_ld_proc"], called_email_ids)

    @freeze_time("2022-12-12 12:00:00")  # Monday
    @mock.patch("leavers.workflow.tasks.ProcessorReminderEmail.get_send_email_method")
    def test_same_ld_and_lwd(self, mock_get_send_email_method):
        self.task2.execute(task_info=self.task_info)
        calls = mock_get_send_email_method.call_args_list

        called_email_ids: List[str] = [call.kwargs["email_id"].value for call in calls]

        self.assertNotIn(self.email_ids["day_after_lwd"], called_email_ids)
        self.assertNotIn(self.email_ids["two_days_after_lwd"], called_email_ids)
        self.assertIn(self.email_ids["on_ld"], called_email_ids)
        self.assertIn(self.email_ids["one_day_after_ld"], called_email_ids)
        self.assertIn(self.email_ids["two_days_after_ld_lm"], called_email_ids)
        self.assertIn(self.email_ids["two_days_after_ld_proc"], called_email_ids)


class TestSREProcessorReminderEmail(TestCase):
    def setUp(self):
        self.user = UserFactory()

        # Leaving Request with different dates
        self.flow = FlowFactory(executed_by=self.user)
        self.task_record = TaskRecordFactory(executed_by=self.user, flow=self.flow)
        self.leaving_request = LeavingRequestFactory(
            last_day=make_aware(datetime(2022, 12, 12)),  # Monday
            leaving_date=make_aware(datetime(2022, 12, 16)),  # Friday
        )
        self.leaving_request.slack_messages.create(
            slack_timestamp="",
            channel_id="",
        )
        self.flow.leaving_request = self.leaving_request
        self.flow.save()

        # Leaving Request with same dates
        self.flow2 = FlowFactory(executed_by=self.user)
        self.task_record2 = TaskRecordFactory(executed_by=self.user, flow=self.flow2)
        self.leaving_request2 = LeavingRequestFactory(
            last_day=make_aware(datetime(2022, 12, 16)),  # Friday
            leaving_date=make_aware(datetime(2022, 12, 16)),  # Friday
        )
        self.leaving_request2.slack_messages.create(
            slack_timestamp="",
            channel_id="",
        )
        self.flow2.leaving_request = self.leaving_request2
        self.flow2.save()

        self.task = ProcessorReminderEmail(self.user, self.task_record, self.flow)
        self.task2 = ProcessorReminderEmail(self.user, self.task_record, self.flow2)
        self.task_info = {"processor_emails": ["someone@example.com"]}  # /PS-IGNORE
        self.email_ids: ReminderEmailDict = SRE_REMINDER_EMAILS
        self.task_info.update(**self.email_ids)

    @freeze_time("2022-12-12 12:00:00")  # Monday
    def test_should_send_email_none_sent_late(self):
        for _, email_id in self.email_ids.items():
            if email_id is not None:
                with self.subTest(email_id=email_id):
                    self.assertTrue(
                        self.task.should_send_email(email_id=EmailIds(email_id))
                    )

    @freeze_time("2022-12-12 12:00:00")  # Monday
    def test_should_send_email_already_sent(self):
        for _, email_id in self.email_ids.items():
            if email_id is not None:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id}",
                )
                with self.subTest(email_id=email_id):
                    self.assertFalse(
                        self.task.should_send_email(email_id=EmailIds(email_id))
                    )

    @freeze_time("2022-12-5 12:00:00")  # Monday
    @mock.patch("core.utils.sre_messages.send_sre_reminder_message")
    def test_early(self, mock_send_sre_reminder_message: mock.MagicMock):
        self.task.execute(task_info=self.task_info)
        mock_send_sre_reminder_message.assert_not_called()

    @freeze_time("2022-12-13 12:00:00")  # Tuesday
    @mock.patch("core.utils.sre_messages.send_sre_reminder_message")
    def test_day_after_lwd(self, mock_send_sre_reminder_message: mock.MagicMock):
        self.task.execute(task_info=self.task_info)
        mock_send_sre_reminder_message.assert_called_once()

    @freeze_time("2022-12-14 12:00:00")  # Wednesday
    @mock.patch("core.utils.sre_messages.send_sre_reminder_message")
    def test_two_days_after_lwd(self, mock_send_sre_reminder_message: mock.MagicMock):
        for _, email_id in self.email_ids.items():
            if email_id != self.email_ids["two_days_after_lwd"]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id}",
                )

        self.task.execute(task_info=self.task_info)
        mock_send_sre_reminder_message.assert_not_called()

    @freeze_time("2022-12-16 12:00:00")  # Friday
    @mock.patch("core.utils.sre_messages.send_sre_reminder_message")
    def test_on_ld(self, mock_send_sre_reminder_message: mock.MagicMock):
        for _, email_id in self.email_ids.items():
            if email_id != self.email_ids["on_ld"]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id}",
                )

        self.task.execute(task_info=self.task_info)
        mock_send_sre_reminder_message.assert_not_called()

    @freeze_time("2022-12-17 12:00:00")  # Saturday
    @mock.patch("core.utils.sre_messages.send_sre_reminder_message")
    def test_one_day_after_ld_weekend(
        self, mock_send_sre_reminder_message: mock.MagicMock
    ):
        for _, email_id in self.email_ids.items():
            if email_id != self.email_ids["one_day_after_ld"]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id}",
                )

        self.task.execute(task_info=self.task_info)
        mock_send_sre_reminder_message.assert_not_called()

    @freeze_time("2022-12-19 12:00:00")  # Monday
    @mock.patch("core.utils.sre_messages.send_sre_reminder_message")
    def test_one_day_after_ld_weekday(
        self, mock_send_sre_reminder_message: mock.MagicMock
    ):
        for _, email_id in self.email_ids.items():
            if email_id != self.email_ids["one_day_after_ld"]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id}",
                )

        self.task.execute(task_info=self.task_info)
        mock_send_sre_reminder_message.assert_called_once()

    @freeze_time("2022-12-18 12:00:00")  # Sunday
    @mock.patch("core.utils.sre_messages.send_sre_reminder_message")
    def test_two_days_after_ld_weekend(
        self, mock_send_sre_reminder_message: mock.MagicMock
    ):
        for _, email_id in self.email_ids.items():
            if email_id not in [
                self.email_ids["two_days_after_ld_lm"],
                self.email_ids["two_days_after_ld_proc"],
            ]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id}",
                )

        self.task.execute(task_info=self.task_info)
        mock_send_sre_reminder_message.assert_not_called()

    @freeze_time("2022-12-19 12:00:00")  # Monday
    @mock.patch("core.utils.sre_messages.send_sre_reminder_message")
    def test_two_days_after_ld_weekday(
        self, mock_send_sre_reminder_message: mock.MagicMock
    ):
        for _, email_id in self.email_ids.items():
            if email_id not in [
                self.email_ids["two_days_after_ld_lm"],
                self.email_ids["two_days_after_ld_proc"],
            ]:
                self.leaving_request.email_task_logs.create(
                    user=self.user,
                    task_name=f"Some task name that contains an Email ID {email_id}",
                )

        self.task.execute(task_info=self.task_info)
        mock_send_sre_reminder_message.assert_called_once()

    @freeze_time("2022-12-19 12:00:00")  # Monday
    @mock.patch("core.utils.sre_messages.send_sre_reminder_message")
    def test_different_ld_and_lwd(self, mock_send_sre_reminder_message: mock.MagicMock):
        self.task.execute(task_info=self.task_info)

        calls = mock_send_sre_reminder_message.call_args_list
        called_email_ids: List[str] = [call.kwargs["email_id"].value for call in calls]

        self.assertIn(self.email_ids["day_after_lwd"], called_email_ids)
        self.assertIn(self.email_ids["one_day_after_ld"], called_email_ids)
        self.assertIn(self.email_ids["two_days_after_ld_proc"], called_email_ids)

    @freeze_time("2022-12-19 12:00:00")  # Monday
    @mock.patch("core.utils.sre_messages.send_sre_reminder_message")
    def test_same_ld_and_lwd(self, mock_send_sre_reminder_message: mock.MagicMock):
        self.task2.execute(task_info=self.task_info)

        calls = mock_send_sre_reminder_message.call_args_list
        called_email_ids: List[str] = [call.kwargs["email_id"].value for call in calls]

        self.assertIn(self.email_ids["one_day_after_ld"], called_email_ids)
        self.assertIn(self.email_ids["two_days_after_ld_proc"], called_email_ids)
