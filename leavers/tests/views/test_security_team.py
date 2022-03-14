from django.contrib.auth.models import Group
from django.test.testcases import TestCase
from django.urls import reverse
from django.utils import timezone

from leavers.factories import LeavingRequestFactory
from leavers.models import LeavingRequest, TaskLog
from leavers.tests.views.include import ViewAccessTest


class TestIncompleteLeavingRequestListing(ViewAccessTest, TestCase):
    view_name = "security-team-listing-incomplete"
    allowed_methods = ["get", "post", "put"]

    def setUp(self) -> None:
        super().setUp()
        # Add the Security Team User Group (and add the authenticated user to it)
        sre_group, _ = Group.objects.get_or_create(name="Security Team")
        self.authenticated_user.groups.add(sre_group.id)

    def test_pagination_one_page(self) -> None:
        LeavingRequestFactory.create_batch(19)

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Showing <b>1</b> to <b>19</b> of <b>19</b> incomplete leaving requests",
        )
        self.assertNotContains(response, '<nav class="pagination')

    def test_pagination_multiple_pages_page_1(self) -> None:
        LeavingRequestFactory.create_batch(50)

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Showing <b>1</b> to <b>20</b> of <b>50</b> incomplete leaving requests",
        )
        self.assertContains(response, '<nav class="pagination')

    def test_pagination_multiple_pages_page_2(self) -> None:
        LeavingRequestFactory.create_batch(50)

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url() + "?page=2")

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Showing <b>21</b> to <b>40</b> of <b>50</b> incomplete leaving requests",
        )
        self.assertContains(response, '<nav class="pagination')

    def test_search(self) -> None:
        LeavingRequestFactory.create_batch(50)
        LeavingRequestFactory(
            leaver_activitystream_user__first_name="Joe",
            leaver_activitystream_user__last_name="Bloggs",
        )

        self.client.force_login(self.authenticated_user)
        response = self.client.post(self.get_url(), {"query": "Joe Bloggs"})

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Joe")
        self.assertContains(response, "Bloggs")
        self.assertContains(response, "Incomplete")


class TestCompleteLeavingRequestListing(ViewAccessTest, TestCase):
    view_name = "security-team-listing-complete"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        # Add the Security Team User Group (and add the authenticated user to it)
        sre_group, _ = Group.objects.get_or_create(name="Security Team")
        self.authenticated_user.groups.add(sre_group.id)

    def test_pagination_one_page(self) -> None:
        LeavingRequestFactory.create_batch(19, security_team_complete=timezone.now())

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Showing <b>1</b> to <b>19</b> of <b>19</b> complete leaving requests",
        )
        self.assertNotContains(response, '<nav class="pagination')

    def test_pagination_multiple_pages_page_1(self) -> None:
        LeavingRequestFactory.create_batch(50, security_team_complete=timezone.now())

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Showing <b>1</b> to <b>20</b> of <b>50</b> complete leaving requests",
        )
        self.assertContains(response, '<nav class="pagination')

    def test_pagination_multiple_pages_page_2(self) -> None:
        LeavingRequestFactory.create_batch(50, security_team_complete=timezone.now())

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url() + "?page=2")

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Showing <b>21</b> to <b>40</b> of <b>50</b> complete leaving requests",
        )
        self.assertContains(response, '<nav class="pagination')

    def test_search(self) -> None:
        LeavingRequestFactory.create_batch(50, security_team_complete=timezone.now())
        LeavingRequestFactory(
            security_team_complete=timezone.now(),
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
    view_name = "security-team-confirmation"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        # Create Leaving Request
        self.leaving_request: LeavingRequest = LeavingRequestFactory()
        # Add the Security Team User Group (and add the authenticated user to it)  /PS-IGNORE
        security_team_group, _ = Group.objects.get_or_create(name="Security Team")
        self.authenticated_user.groups.add(security_team_group.id)
        # Update the view_kwargs to pass the leaving_request ID to the view.
        self.view_kwargs = {"args": [self.leaving_request.uuid]}

    def assert_authenticated_pass(self, method: str, response):
        if method in ["post", "put"]:
            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                response.url,
                reverse("security-team-thank-you", args=[self.leaving_request.uuid]),
            )
        else:
            super().assert_authenticated_pass(method=method, response=response)

    def test_page_contents(self):
        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        self.assertEqual(
            response.context["leaver_name"], self.leaving_request.get_leaver_name()
        )
        self.assertEqual(
            response.context["leaving_date"], self.leaving_request.last_day
        )

    def test_submit_form(self):
        self.client.force_login(self.authenticated_user)
        self.client.post(
            self.get_url(),
            {
                "security_pass": "returned",
                "rosa_laptop_returned": True,
                "rosa_key_returned": True,
            },
        )

        # Check the task logs are created
        user_task_logs = TaskLog.objects.filter(user=self.authenticated_user)
        self.assertTrue(user_task_logs.exists())
        task_names = [
            "Security pass returned confirmed",
            "ROSA laptop return confirmed",
            "ROSA key return confirmed",
        ]
        for task_name in task_names:
            self.assertTrue(user_task_logs.filter(task_name=task_name).exists())


class TestThankYouView(ViewAccessTest, TestCase):
    view_name = "security-team-thank-you"
    allowed_methods = ["get"]

    def setUp(self):
        super().setUp()
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

        leaver_name = self.leaving_request.get_leaver_name()
        self.assertEqual(response.context["leaver_name"], leaver_name)
