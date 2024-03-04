from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from leavers.factories import LeavingRequestFactory
from leavers.tasks import weekly_leavers_email


class TestWeeklyLeaversEmail(TestCase):
    # Monday
    @freeze_time("2023-02-13 12:00:00")
    @mock.patch("leavers.tasks.send_workforce_planning_leavers_email")
    def test_monday(self, mock_send_workforce_planning_leavers_email):
        weekly_leavers_email()
        mock_send_workforce_planning_leavers_email.assert_called_once()

    # Tuesday
    @freeze_time("2023-02-14 12:00:00")
    @mock.patch("leavers.tasks.send_workforce_planning_leavers_email")
    def test_tuesday(self, mock_send_workforce_planning_leavers_email):
        weekly_leavers_email()
        mock_send_workforce_planning_leavers_email.assert_not_called()

    # Wednesday
    @freeze_time("2023-02-15 12:00:00")
    @mock.patch("leavers.tasks.send_workforce_planning_leavers_email")
    def test_wednesday(self, mock_send_workforce_planning_leavers_email):
        weekly_leavers_email()
        mock_send_workforce_planning_leavers_email.assert_not_called()

    # Thursday
    @freeze_time("2023-02-16 12:00:00")
    @mock.patch("leavers.tasks.send_workforce_planning_leavers_email")
    def test_thursday(self, mock_send_workforce_planning_leavers_email):
        weekly_leavers_email()
        mock_send_workforce_planning_leavers_email.assert_not_called()

    # Friday
    @freeze_time("2023-02-17 12:00:00")
    @mock.patch("leavers.tasks.send_workforce_planning_leavers_email")
    def test_friday(self, mock_send_workforce_planning_leavers_email):
        weekly_leavers_email()
        mock_send_workforce_planning_leavers_email.assert_not_called()

    # Saturday
    @freeze_time("2023-02-18 12:00:00")
    @mock.patch("leavers.tasks.send_workforce_planning_leavers_email")
    def test_saturday(self, mock_send_workforce_planning_leavers_email):
        weekly_leavers_email()
        mock_send_workforce_planning_leavers_email.assert_not_called()

    # Sunday
    @freeze_time("2023-02-19 12:00:00")
    @mock.patch("leavers.tasks.send_workforce_planning_leavers_email")
    def test_sunday(self, mock_send_workforce_planning_leavers_email):
        weekly_leavers_email()
        mock_send_workforce_planning_leavers_email.assert_not_called()

    # Monday - no leavers
    @freeze_time("2023-02-13 12:00:00")
    @mock.patch("leavers.tasks.send_workforce_planning_leavers_email")
    def test_no_leavers(self, mock_send_workforce_planning_leavers_email):
        weekly_leavers_email()
        # Make sure the function is called with the right kwargs
        call = mock_send_workforce_planning_leavers_email.call_args_list[0]
        self.assertEqual(call[1]["week_ending"], "12/02/2023")
        self.assertEqual(call[1]["leaving_requests"].count(), 0)

    # Monday - with leavers
    @freeze_time("2023-02-13 12:00:00")
    @mock.patch("leavers.tasks.send_workforce_planning_leavers_email")
    def test_with_leavers(self, mock_send_workforce_planning_leavers_email):
        LeavingRequestFactory.create_batch(
            3,
            line_manager_complete=timezone.now(),
            leaving_date=timezone.now() - timedelta(days=5),
        )
        weekly_leavers_email()
        # Make sure the function is called with the right kwargs
        call = mock_send_workforce_planning_leavers_email.call_args_list[0]
        self.assertEqual(call[1]["week_ending"], "12/02/2023")
        self.assertEqual(call[1]["leaving_requests"].count(), 3)
