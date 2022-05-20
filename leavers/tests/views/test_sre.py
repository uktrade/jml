from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import Group
from django.test.testcases import TestCase
from django.utils import timezone

from leavers.factories import LeavingRequestFactory, SlackMessageFactory
from leavers.forms.leaver import SecurityClearance
from leavers.models import TaskLog
from leavers.tests.views.include import ViewAccessTest


class TestIncompleteLeavingRequestListing(ViewAccessTest, TestCase):
    view_name = "sre-listing-incomplete"
    allowed_methods = ["get", "post", "put"]

    def setUp(self) -> None:
        super().setUp()
        # Add the SRE User Group (and add the authenticated user to it)
        sre_group, _ = Group.objects.get_or_create(name="SRE")
        self.authenticated_user.groups.add(sre_group.id)

    def test_pagination_one_page(self) -> None:
        LeavingRequestFactory.create_batch(
            19,
            line_manager_complete=timezone.now(),
            leaving_date=timezone.now() + timedelta(days=1),
            last_day=timezone.now() + timedelta(days=1),
            security_clearance=SecurityClearance.SC.value,
        )

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Showing <b>1</b> to <b>19</b> of <b>19</b> outstanding leaving requests",
        )
        self.assertNotContains(response, '<nav class="pagination')

    def test_pagination_multiple_pages_page_1(self) -> None:
        LeavingRequestFactory.create_batch(
            50,
            line_manager_complete=timezone.now(),
            leaving_date=timezone.now() + timedelta(days=1),
            last_day=timezone.now() + timedelta(days=1),
            security_clearance=SecurityClearance.SC.value,
        )

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Showing <b>1</b> to <b>20</b> of <b>50</b> outstanding leaving requests",
        )
        self.assertContains(response, '<nav class="pagination')

    def test_pagination_multiple_pages_page_2(self) -> None:
        LeavingRequestFactory.create_batch(
            50,
            line_manager_complete=timezone.now(),
            leaving_date=timezone.now() + timedelta(days=1),
            last_day=timezone.now() + timedelta(days=1),
            security_clearance=SecurityClearance.SC.value,
        )

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url() + "?page=2")

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Showing <b>21</b> to <b>40</b> of <b>50</b> outstanding leaving requests",
        )
        self.assertContains(response, '<nav class="pagination')

    def test_search(self) -> None:
        LeavingRequestFactory.create_batch(
            50,
            line_manager_complete=timezone.now(),
            leaving_date=timezone.now() + timedelta(days=1),
            last_day=timezone.now() + timedelta(days=1),
            security_clearance=SecurityClearance.SC.value,
        )
        LeavingRequestFactory(
            line_manager_complete=timezone.now(),
            leaving_date=timezone.now() + timedelta(days=1),
            last_day=timezone.now() + timedelta(days=1),
            security_clearance=SecurityClearance.SC.value,
            leaver_activitystream_user__first_name="Joe",
            leaver_activitystream_user__last_name="Bloggs",
        )

        self.client.force_login(self.authenticated_user)
        response = self.client.post(self.get_url(), {"query": "Joe Bloggs"})

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Joe")
        self.assertContains(response, "Bloggs")
        self.assertContains(response, "Outstanding")


class TestCompleteLeavingRequestListing(ViewAccessTest, TestCase):
    view_name = "sre-listing-complete"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        # Add the SRE User Group (and add the authenticated user to it)
        sre_group, _ = Group.objects.get_or_create(name="SRE")
        self.authenticated_user.groups.add(sre_group.id)

    def test_pagination_one_page(self) -> None:
        LeavingRequestFactory.create_batch(
            19,
            line_manager_complete=timezone.now(),
            sre_complete=timezone.now(),
            leaving_date=timezone.now() + timedelta(days=1),
            last_day=timezone.now() + timedelta(days=1),
            security_clearance=SecurityClearance.SC.value,
        )

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Showing <b>1</b> to <b>19</b> of <b>19</b> complete leaving requests",
        )
        self.assertNotContains(response, '<nav class="pagination')

    def test_pagination_multiple_pages_page_1(self) -> None:
        LeavingRequestFactory.create_batch(
            50,
            line_manager_complete=timezone.now(),
            sre_complete=timezone.now(),
            leaving_date=timezone.now() + timedelta(days=1),
            last_day=timezone.now() + timedelta(days=1),
            security_clearance=SecurityClearance.SC.value,
        )

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Showing <b>1</b> to <b>20</b> of <b>50</b> complete leaving requests",
        )
        self.assertContains(response, '<nav class="pagination')

    def test_pagination_multiple_pages_page_2(self) -> None:
        LeavingRequestFactory.create_batch(
            50,
            line_manager_complete=timezone.now(),
            sre_complete=timezone.now(),
            leaving_date=timezone.now() + timedelta(days=1),
            last_day=timezone.now() + timedelta(days=1),
            security_clearance=SecurityClearance.SC.value,
        )

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url() + "?page=2")

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Showing <b>21</b> to <b>40</b> of <b>50</b> complete leaving requests",
        )
        self.assertContains(response, '<nav class="pagination')

    def test_search(self) -> None:
        LeavingRequestFactory.create_batch(
            50,
            line_manager_complete=timezone.now(),
            sre_complete=timezone.now(),
            leaving_date=timezone.now() + timedelta(days=1),
            last_day=timezone.now() + timedelta(days=1),
            security_clearance=SecurityClearance.SC.value,
        )
        LeavingRequestFactory(
            line_manager_complete=timezone.now(),
            sre_complete=timezone.now(),
            leaving_date=timezone.now() + timedelta(days=1),
            last_day=timezone.now() + timedelta(days=1),
            security_clearance=SecurityClearance.SC.value,
            leaver_activitystream_user__first_name="Joe",
            leaver_activitystream_user__last_name="Bloggs",
        )

        self.client.force_login(self.authenticated_user)
        response = self.client.post(self.get_url(), {"query": "Joe Bloggs"})

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Joe")
        self.assertContains(response, "Bloggs")
        self.assertContains(response, "Complete")


class TestTaskConfirmationView(ViewAccessTest, TestCase):
    view_name = "sre-confirmation"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        # Create Leaving Request (with initial Slack message)
        self.leaving_request = LeavingRequestFactory(
            line_manager_complete=timezone.now(),
            leaving_date=timezone.now() + timedelta(days=1),
            last_day=timezone.now() + timedelta(days=1),
            security_clearance=SecurityClearance.SC.value,
        )
        SlackMessageFactory(leaving_request=self.leaving_request)
        # Add the SRE User Group (and add the authenticated user to it)  /PS-IGNORE
        sre_group, _ = Group.objects.get_or_create(name="SRE")
        self.authenticated_user.groups.add(sre_group.id)
        # Update the view_kwargs to pass the leaving_request ID to the view.
        self.view_kwargs = {"args": [self.leaving_request.uuid]}

    def test_page_contents(self):
        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        leaver_name = self.leaving_request.get_leaver_name()
        self.assertEqual(response.context["leaver_name"], leaver_name)
        self.assertEqual(
            response.context["leaving_date"], self.leaving_request.last_day.date()
        )

    @mock.patch("leavers.views.sre.send_sre_complete_message")
    def test_save_form(self, mock_send_sre_complete_message):
        self.client.force_login(self.authenticated_user)
        self.client.post(
            self.get_url(),
            {},
        )

        self.leaving_request.refresh_from_db()

        # Check that the leaving request has NOT been marked as SRE complete
        self.assertFalse(self.leaving_request.sre_complete)

    @mock.patch("leavers.views.sre.send_sre_complete_message")
    def test_submit_form(self, mock_send_sre_complete_message):
        self.client.force_login(self.authenticated_user)
        self.client.post(
            self.get_url(),
            {
                "submit": "",
                "vpn": True,
                "govuk_paas": True,
                "github": True,
                "sentry": True,
                "slack": True,
                "sso": True,
                "aws": True,
                "jira": True,
            },
        )

        self.leaving_request.refresh_from_db()

        # Check that the leaving request has been marked as SRE complete
        self.assertTrue(self.leaving_request.sre_complete)

        # Check the SRE Complete message is triggered
        mock_send_sre_complete_message.assert_called_once()

        # Check the task logs are created
        user_task_logs = TaskLog.objects.filter(user=self.authenticated_user)
        self.assertTrue(user_task_logs.exists())
        self.assertTrue(
            user_task_logs.filter(
                task_name="VPN access removal confirmed",
            ).exists()
        )
        self.assertTrue(
            user_task_logs.filter(
                task_name="GOV.UK PAAS access removal confirmed",
            ).exists()
        )
        self.assertTrue(
            user_task_logs.filter(
                task_name="Github access removal confirmed",
            ).exists()
        )
        self.assertTrue(
            user_task_logs.filter(
                task_name="Sentry access removal confirmed",
            ).exists()
        )
        self.assertTrue(
            user_task_logs.filter(
                task_name="Slack access removal confirmed",
            ).exists()
        )
        self.assertTrue(
            user_task_logs.filter(
                task_name="SSO access removal confirmed",
            ).exists()
        )
        self.assertTrue(
            user_task_logs.filter(
                task_name="AWS access removal confirmed",
            ).exists()
        )
        self.assertTrue(
            user_task_logs.filter(
                task_name="Jira access removal confirmed",
            ).exists()
        )


class TestThankYouView(ViewAccessTest, TestCase):
    view_name = "sre-thank-you"
    allowed_methods = ["get"]

    def setUp(self):
        super().setUp()
        # Create Leaving Request (with initial Slack message)
        self.leaving_request = LeavingRequestFactory(
            line_manager_complete=timezone.now()
        )
        SlackMessageFactory(leaving_request=self.leaving_request)
        # Add the SRE User Group (and add the authenticated user to it)  /PS-IGNORE
        sre_group, _ = Group.objects.get_or_create(name="SRE")
        self.authenticated_user.groups.add(sre_group.id)
        # Update the view_kwargs to pass the leaving_request ID to the view.
        self.view_kwargs = {"args": [self.leaving_request.uuid]}

    def test_page_contents(self):
        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        leaver_name = self.leaving_request.get_leaver_name()
        self.assertEqual(response.context["leaver_name"], leaver_name)
