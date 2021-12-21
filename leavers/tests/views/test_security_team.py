from django.contrib.auth.models import Group
from django.test.testcases import TestCase

from leavers.factories import LeavingRequestFactory  # /PS-IGNORE
from leavers.models import TaskLog
from leavers.tests.views.include import ViewAccessTest


class TestTaskConfirmationView(ViewAccessTest, TestCase):
    view_name = "security-team-confirmation"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()  # /PS-IGNORE
        # Create Leaving Request
        self.leaving_request = LeavingRequestFactory()
        # Add the Security Team User Group (and add the authenticated user to it)  /PS-IGNORE
        security_team_group, _ = Group.objects.get_or_create(name="Security Team")
        self.authenticated_user.groups.add(security_team_group.id)
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

    def test_submit_form(self):
        self.client.force_login(self.authenticated_user)
        self.client.post(
            self.get_url(),
            {
                "building_pass_access_revoked": True,
                "rosa_access_revoked": True,
            },
        )

        # Check the task logs are created
        user_task_logs = TaskLog.objects.filter(
            user=self.authenticated_user  # /PS-IGNORE
        )
        self.assertTrue(user_task_logs.exists())


class TestThankYouView(ViewAccessTest, TestCase):
    view_name = "security-team-thank-you"
    allowed_methods = ["get"]

    def setUp(self):
        super().setUp()  # /PS-IGNORE
        # Create Leaving Request (with initial Slack message)
        self.leaving_request = LeavingRequestFactory()
        # Add the Security Team User Group (and add the authenticated user to it)  /PS-IGNORE
        security_team_group, _ = Group.objects.get_or_create(name="Security Team")
        self.authenticated_user.groups.add(security_team_group.id)
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
