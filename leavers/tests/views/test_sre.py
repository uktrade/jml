from unittest import mock

from django.contrib.auth.models import Group
from django.test.testcases import TestCase

from leavers.factories import LeavingRequestFactory, SlackMessageFactory
from leavers.models import TaskLog
from leavers.tests.views.include import ViewAccessTest


class TestIncompleteLeavingRequestListing(ViewAccessTest, TestCase):
    view_name = "sre-listing-incomplete"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        # Add the SRE User Group (and add the authenticated user to it)  /PS-IGNORE
        sre_group, _ = Group.objects.get_or_create(name="SRE")
        self.authenticated_user.groups.add(sre_group.id)


class TestCompleteLeavingRequestListing(ViewAccessTest, TestCase):
    view_name = "sre-listing-complete"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        # Add the SRE User Group (and add the authenticated user to it)  /PS-IGNORE
        sre_group, _ = Group.objects.get_or_create(name="SRE")
        self.authenticated_user.groups.add(sre_group.id)


class TestTaskConfirmationView(ViewAccessTest, TestCase):
    view_name = "sre-confirmation"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        # Create Leaving Request (with initial Slack message)
        self.leaving_request = LeavingRequestFactory()
        SlackMessageFactory(leaving_request=self.leaving_request)
        # Add the SRE User Group (and add the authenticated user to it)  /PS-IGNORE
        sre_group, _ = Group.objects.get_or_create(name="SRE")
        self.authenticated_user.groups.add(sre_group.id)
        # Update the view_kwargs to pass the leaving_request ID to the view.
        self.view_kwargs = {"args": [self.leaving_request.uuid]}

    def test_page_contents(self):
        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        leaver_first_name = self.leaving_request.leaver_first_name
        leaver_last_name = self.leaving_request.leaver_last_name
        self.assertEqual(
            response.context["leaver_name"], f"{leaver_first_name} {leaver_last_name}"
        )
        self.assertEqual(
            response.context["leaving_date"], self.leaving_request.last_day
        )

    @mock.patch("leavers.views.sre.send_sre_complete_message")
    def test_submit_form(self, mock_send_sre_complete_message):
        self.client.force_login(self.authenticated_user)
        self.client.post(
            self.get_url(),
            {
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

        # Check the SRE Complete message is triggered
        mock_send_sre_complete_message.assert_called_once()

        # Check the task logs are created
        user_task_logs = TaskLog.objects.filter(user=self.authenticated_user)
        self.assertTrue(user_task_logs.exists())
        self.assertTrue(
            user_task_logs.filter(
                task_name="VPN access removed",
            ).exists()
        )
        self.assertTrue(
            user_task_logs.filter(
                task_name="GOV.UK PAAS access removed",
            ).exists()
        )
        self.assertTrue(
            user_task_logs.filter(
                task_name="Github access removed",
            ).exists()
        )
        self.assertTrue(
            user_task_logs.filter(
                task_name="Sentry access removed",
            ).exists()
        )
        self.assertTrue(
            user_task_logs.filter(
                task_name="Slack access removed",
            ).exists()
        )
        self.assertTrue(
            user_task_logs.filter(
                task_name="SSO access removed",
            ).exists()
        )
        self.assertTrue(
            user_task_logs.filter(
                task_name="AWS access removed",
            ).exists()
        )
        self.assertTrue(
            user_task_logs.filter(
                task_name="Jira access removed",
            ).exists()
        )


class TestThankYouView(ViewAccessTest, TestCase):
    view_name = "sre-thank-you"
    allowed_methods = ["get"]

    def setUp(self):
        super().setUp()
        # Create Leaving Request (with initial Slack message)
        self.leaving_request = LeavingRequestFactory()
        SlackMessageFactory(leaving_request=self.leaving_request)
        # Add the SRE User Group (and add the authenticated user to it)  /PS-IGNORE
        sre_group, _ = Group.objects.get_or_create(name="SRE")
        self.authenticated_user.groups.add(sre_group.id)
        # Update the view_kwargs to pass the leaving_request ID to the view.
        self.view_kwargs = {"args": [self.leaving_request.uuid]}

    def test_page_contents(self):
        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        leaver_first_name = self.leaving_request.leaver_first_name
        leaver_last_name = self.leaving_request.leaver_last_name
        self.assertEqual(
            response.context["leaver_name"], f"{leaver_first_name} {leaver_last_name}"
        )
