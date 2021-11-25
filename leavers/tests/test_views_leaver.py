from datetime import date
from unittest import mock
from unittest.case import skip

from django.test import TestCase
from django.urls import reverse

from leavers import factories, models, types
from leavers.views.leaver import LeaverDetailsMixin
from user.test.factories import UserFactory

PEOPLE_FINDER_RESULT = {
    "first_name": "Joe",
    "last_name": "Bloggs",
    "grade": "Example Grade",
    "primary_phone_number": "0987654321",
    "email": "joe.bloggs@example.com",
    "photo": "",
    "roles": [{"job_title": "Example Job Title", "team": {"name": "Example Team"}}],
}


class TestLeaverDetailsMixin(TestCase):

    """
    Tests for `get_leaver_details`
    """

    @mock.patch("leavers.views.leaver.search_people_finder", return_value=[])
    def test_get_leaver_details_no_results(self, mock_search_people_finder):
        with self.assertRaisesMessage(Exception, "Issue finding user in People Finder"):
            LeaverDetailsMixin().get_leaver_details(email="")

    @mock.patch(
        "leavers.views.leaver.search_people_finder", return_value=[PEOPLE_FINDER_RESULT]
    )
    def test_get_leaver_details_with_result(self, mock_search_people_finder):
        leaver_details = LeaverDetailsMixin().get_leaver_details(email="")
        self.assertEqual(
            leaver_details["first_name"], PEOPLE_FINDER_RESULT["first_name"]
        )
        self.assertEqual(leaver_details["last_name"], PEOPLE_FINDER_RESULT["last_name"])
        self.assertEqual(leaver_details["grade"], PEOPLE_FINDER_RESULT["grade"])
        self.assertEqual(
            leaver_details["personal_phone"],
            PEOPLE_FINDER_RESULT["primary_phone_number"],
        )
        self.assertEqual(leaver_details["work_email"], PEOPLE_FINDER_RESULT["email"])
        self.assertEqual(
            leaver_details["job_title"],
            PEOPLE_FINDER_RESULT["roles"][0]["job_title"],
        )
        self.assertEqual(
            leaver_details["team_name"],
            PEOPLE_FINDER_RESULT["roles"][0]["team"]["name"],
        )

    @mock.patch(
        "leavers.views.leaver.search_people_finder", return_value=[PEOPLE_FINDER_RESULT]
    )
    def test_get_leaver_details_existing_updates(self, mock_search_people_finder):
        factories.LeaverUpdatesFactory(
            leaver_email="joe.bloggs@example.com", updates={"first_name": "Joey"}
        )
        leaver_details = LeaverDetailsMixin().get_leaver_details(
            email="joe.bloggs@example.com"
        )
        self.assertNotEqual(leaver_details["first_name"], "Joey")

    """
    Tests for `get_leaver_detail_updates`
    """

    def test_get_leaver_detail_updates_no_updates(self):
        leaver_detail_updates = LeaverDetailsMixin().get_leaver_detail_updates(
            email="joe.bloggs@example.com"
        )
        self.assertEqual(leaver_detail_updates, {})

    def test_get_leaver_detail_updates_some_updates(self):
        factories.LeaverUpdatesFactory(
            leaver_email="joe.bloggs@example.com", updates={"first_name": "Joey"}
        )
        leaver_detail_updates = LeaverDetailsMixin().get_leaver_detail_updates(
            email="joe.bloggs@example.com"
        )
        self.assertEqual(leaver_detail_updates, {"first_name": "Joey"})

    """
    Tests for `store_leaver_detail_updates`
    """

    @mock.patch(
        "leavers.views.leaver.search_people_finder", return_value=[PEOPLE_FINDER_RESULT]
    )
    def store_leaver_detail_updates_no_changes(self, mock_search_people_finder):
        LeaverDetailsMixin().store_leaver_detail_updates(
            email="joe.bloggs@example.com", updates={}
        )
        self.assertEqual(
            models.LeaverUpdates.objects.filter(
                leaver_email="joe.bloggs@example.com"
            ).count(),
            1,
        )

    @mock.patch(
        "leavers.views.leaver.search_people_finder", return_value=[PEOPLE_FINDER_RESULT]
    )
    def store_leaver_detail_updates_some_changes(self, mock_search_people_finder):
        LeaverDetailsMixin().store_leaver_detail_updates(
            email="joe.bloggs@example.com", updates={"first_name": "Joey"}
        )

        leaver_updates = models.LeaverUpdates.objects.get(
            leaver_email="joe.bloggs@example.com",
        )
        self.assertEqual(leaver_updates.updates, {"first_name": "Joey"})

    """
    Tests for `get_leaver_details_with_updates`
    """

    @mock.patch(
        "leavers.views.leaver.search_people_finder", return_value=[PEOPLE_FINDER_RESULT]
    )
    def test_get_leaver_details_with_updates_no_updates(
        self, mock_search_people_finder
    ):
        leaver_details = LeaverDetailsMixin().get_leaver_details_with_updates(
            email="joe.bloggs@example.com"
        )
        self.assertEqual(leaver_details["first_name"], "Joe")

    @mock.patch(
        "leavers.views.leaver.search_people_finder", return_value=[PEOPLE_FINDER_RESULT]
    )
    def test_get_leaver_details_with_updates_some_updates(
        self, mock_search_people_finder
    ):
        factories.LeaverUpdatesFactory(
            leaver_email="joe.bloggs@example.com", updates={"first_name": "Joey"}
        )
        leaver_details = LeaverDetailsMixin().get_leaver_details_with_updates(
            email="joe.bloggs@example.com"
        )
        self.assertEqual(leaver_details["first_name"], "Joey")

    """
    Tests for `has_required_leaver_details`
    """

    # TODO: Remove skip when required_keys is defined
    @skip
    @mock.patch(
        "leavers.views.leaver.search_people_finder", return_value=[PEOPLE_FINDER_RESULT]
    )
    def test_has_required_leaver_details(self, mock_search_people_finder):
        # No details
        self.assertFalse(
            LeaverDetailsMixin().has_required_leaver_details(leaver_details={})
        )
        # Some of the required details are missing
        self.assertFalse(
            LeaverDetailsMixin().has_required_leaver_details(leaver_details={})
        )
        # All of the required details are present
        self.assertTrue(
            LeaverDetailsMixin().has_required_leaver_details(leaver_details={})
        )


@mock.patch(
    "leavers.views.leaver.search_people_finder", return_value=[PEOPLE_FINDER_RESULT]
)
class TestConfirmDetailsView(TestCase):
    view_name = "leaver-confirm-details"

    def test_unauthenticated_user(self, mock_search_people_finder):
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 302)

    def test_authenticated_user(self, mock_search_people_finder):
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Leaver details confirmation")
        self.assertEqual(
            response.context["leaver_details"],
            {
                "date_of_birth": date(2021, 11, 25),
                "department": "",
                "directorate": "",
                "first_name": "Joe",
                "grade": "Example Grade",
                "job_title": "Example Job Title",
                "last_name": "Bloggs",
                "manager": "",
                "personal_address": "",
                "personal_email": "",
                "personal_phone": "0987654321",
                "photo": "",
                "team_name": "Example Team",
                "work_email": "joe.bloggs@example.com",
            },
        )

    def test_existing_updates(self, mock_search_people_finder):
        user = UserFactory()
        updates: types.LeaverDetailUpdates = {
            "department": "Updated Department",
            "directorate": "Updated Directorate",
            "first_name": "UpdatedFirstName",
            "grade": "Updated Grade",
            "job_title": "Updated Job Title",
            "last_name": "UpdatedLastName",
            "manager": "Updated Manager",
            "personal_address": "Updated Address",
            "personal_email": "Updated Personal Email",
            "personal_phone": "Updated Number",
            "team_name": "Updated Team",
            "work_email": "Updated Work Email",
        }
        factories.LeaverUpdatesFactory(leaver_email=user.email, updates=updates)
        self.client.force_login(user)
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Leaver details confirmation")
        self.assertEqual(
            response.context["leaver_details"],
            {
                "date_of_birth": date(2021, 11, 25),
                "photo": "",
                "department": updates["department"],
                "directorate": updates["directorate"],
                "first_name": updates["first_name"],
                "grade": updates["grade"],
                "job_title": updates["job_title"],
                "last_name": updates["last_name"],
                "manager": updates["manager"],
                "personal_address": updates["personal_address"],
                "personal_email": updates["personal_email"],
                "personal_phone": updates["personal_phone"],
                "team_name": updates["team_name"],
                "work_email": updates["work_email"],
            },
        )


@mock.patch(
    "leavers.views.leaver.search_people_finder", return_value=[PEOPLE_FINDER_RESULT]
)
class TestUpdateDetailsView(TestCase):
    view_name = "leaver-update-details"

    def test_unauthenticated_user(self, mock_search_people_finder):
        response = self.client.get(reverse(self.view_name))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user(self, mock_search_people_finder):
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit leaver details")
        form = response.context["form"]
        self.assertEqual(
            form.initial,
            {
                "date_of_birth": date(2021, 11, 25),
                "department": "",
                "directorate": "",
                "first_name": "Joe",
                "grade": "Example Grade",
                "job_title": "Example Job Title",
                "last_name": "Bloggs",
                "manager": "",
                "personal_address": "",
                "personal_email": "",
                "personal_phone": "0987654321",
                "photo": "",
                "team_name": "Example Team",
                "work_email": "joe.bloggs@example.com",
            },
        )

    def test_existing_updates(self, mock_search_people_finder):
        user = UserFactory()
        updates: types.LeaverDetailUpdates = {
            "department": "Updated Department",
            "directorate": "Updated Directorate",
            "first_name": "UpdatedFirstName",
            "grade": "Updated Grade",
            "job_title": "Updated Job Title",
            "last_name": "UpdatedLastName",
            "manager": "Updated Manager",
            "personal_address": "Updated Address",
            "personal_email": "Updated Personal Email",
            "personal_phone": "Updated Number",
            "team_name": "Updated Team",
            "work_email": "Updated Work Email",
        }
        factories.LeaverUpdatesFactory(leaver_email=user.email, updates=updates)
        self.client.force_login(user)
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit leaver details")
        form = response.context["form"]
        self.assertEqual(
            form.initial,
            {
                "date_of_birth": date(2021, 11, 25),
                "photo": "",
                "department": updates["department"],
                "directorate": updates["directorate"],
                "first_name": updates["first_name"],
                "grade": updates["grade"],
                "job_title": updates["job_title"],
                "last_name": updates["last_name"],
                "manager": updates["manager"],
                "personal_address": updates["personal_address"],
                "personal_email": updates["personal_email"],
                "personal_phone": updates["personal_phone"],
                "team_name": updates["team_name"],
                "work_email": updates["work_email"],
            },
        )
