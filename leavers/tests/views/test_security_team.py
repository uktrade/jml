from datetime import timedelta

from django.contrib.auth.models import Group
from django.test.testcases import TestCase
from django.utils import timezone

from leavers.factories import LeavingRequestFactory
from leavers.forms.leaver import SecurityClearance
from leavers.tests.views.include import LeavingRequestListingViewAccessTest


class TestIncompleteLeavingRequestListing(
    LeavingRequestListingViewAccessTest, TestCase
):
    view_name = "security-team-listing-incomplete"
    allowed_methods = ["get", "post", "put"]

    def setUp(self) -> None:
        super().setUp()
        # Add the Security Team User Group (and add the authenticated user to it)
        sre_group, _ = Group.objects.get_or_create(name="Security Team")
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

        self.assertNotContains(
            response,
            '<nav class="govuk-pagination" aria-label="Pagination">',
        )

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
            "Showing <b>1</b> to <b>30</b> of <b>50</b> outstanding leaving requests",
        )
        self.assertContains(
            response,
            '<nav class="govuk-pagination" aria-label="Pagination">',
        )

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
            "Showing <b>31</b> to <b>50</b> of <b>50</b> outstanding leaving requests",
        )
        self.assertContains(
            response,
            '<nav class="govuk-pagination" aria-label="Pagination">',
        )

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
        response = self.client.post(
            self.get_url(), {"query": "Joe Bloggs"}, follow=True
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Joe")
        self.assertContains(response, "Bloggs")


class TestCompleteLeavingRequestListing(LeavingRequestListingViewAccessTest, TestCase):
    view_name = "security-team-listing-complete"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        # Add the Security Team User Group (and add the authenticated user to it)
        sre_group, _ = Group.objects.get_or_create(name="Security Team")
        self.authenticated_user.groups.add(sre_group.id)

    def test_pagination_one_page(self) -> None:
        LeavingRequestFactory.create_batch(
            19,
            line_manager_complete=timezone.now(),
            security_team_building_pass_complete=timezone.now(),
            security_team_rosa_kit_complete=timezone.now(),
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
        self.assertNotContains(
            response,
            '<nav class="govuk-pagination" aria-label="Pagination">',
        )

    def test_pagination_multiple_pages_page_1(self) -> None:
        LeavingRequestFactory.create_batch(
            50,
            line_manager_complete=timezone.now(),
            security_team_building_pass_complete=timezone.now(),
            security_team_rosa_kit_complete=timezone.now(),
            leaving_date=timezone.now() + timedelta(days=1),
            last_day=timezone.now() + timedelta(days=1),
            security_clearance=SecurityClearance.SC.value,
        )

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Showing <b>1</b> to <b>30</b> of <b>50</b> complete leaving requests",
        )
        self.assertContains(
            response,
            '<nav class="govuk-pagination" aria-label="Pagination">',
        )

    def test_pagination_multiple_pages_page_2(self) -> None:
        LeavingRequestFactory.create_batch(
            50,
            line_manager_complete=timezone.now(),
            security_team_building_pass_complete=timezone.now(),
            security_team_rosa_kit_complete=timezone.now(),
            leaving_date=timezone.now() + timedelta(days=1),
            last_day=timezone.now() + timedelta(days=1),
            security_clearance=SecurityClearance.SC.value,
        )

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url() + "?page=2")

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Showing <b>31</b> to <b>50</b> of <b>50</b> complete leaving requests",
        )
        self.assertContains(
            response,
            '<nav class="govuk-pagination" aria-label="Pagination">',
        )

    def test_search(self) -> None:
        LeavingRequestFactory.create_batch(
            50,
            line_manager_complete=timezone.now(),
            security_team_building_pass_complete=timezone.now(),
            security_team_rosa_kit_complete=timezone.now(),
            leaving_date=timezone.now() + timedelta(days=1),
            last_day=timezone.now() + timedelta(days=1),
            security_clearance=SecurityClearance.SC.value,
        )
        LeavingRequestFactory(
            line_manager_complete=timezone.now(),
            security_team_building_pass_complete=timezone.now(),
            security_team_rosa_kit_complete=timezone.now(),
            leaving_date=timezone.now() + timedelta(days=1),
            last_day=timezone.now() + timedelta(days=1),
            security_clearance=SecurityClearance.SC.value,
            leaver_activitystream_user__first_name="Joe",
            leaver_activitystream_user__last_name="Bloggs",
        )

        self.client.force_login(self.authenticated_user)
        response = self.client.post(
            self.get_url(), {"query": "Joe Bloggs"}, follow=True
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Joe")
        self.assertContains(response, "Bloggs")
        self.assertContains(response, "Complete")
