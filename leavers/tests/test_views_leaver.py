from datetime import date
from unittest import mock

from django.test import TestCase

from leavers import factories, models, types
from leavers.views.leaver import LeaverDetailsMixin


class TestLeaverDetailsMixin(TestCase):
    people_finder_result = {
        "first_name": "Joe",
        "last_name": "Bloggs",
        "grade": "Example Grade",
        "primary_phone_number": "0987654321",
        "email": "joe.bloggs@example.com",
        "photo": "",
        "roles": [{"job_title": "Example Job Title", "team": {"name": "Example Team"}}],
    }
    leaver_details: types.LeaverDetails = {
        # Personal details
        "first_name": "Joe",
        "last_name": "Bloggs",
        "date_of_birth": date(1990, 1, 1),
        "personal_email": "",
        "personal_phone": "",
        "personal_address": "",
        # Professional details
        "grade": "Example Grade",
        "job_title": "",
        "directorate": "",
        "department": "",
        "team_name": "",
        "work_email": "joe.bloggs@example.com",
        "manager": "",
        # Misc.
        "photo": "",
    }

    """
    Tests for `get_leaver_details`
    """

    @mock.patch("leavers.views.leaver.search_people_finder", return_value=[])
    def test_get_leaver_details_no_results(self, mock_search_people_finder):
        with self.assertRaisesMessage(Exception, "Issue finding user in People Finder"):
            LeaverDetailsMixin().get_leaver_details(email="")

    @mock.patch(
        "leavers.views.leaver.search_people_finder", return_value=[people_finder_result]
    )
    def test_get_leaver_details_with_result(self, mock_search_people_finder):
        leaver_details = LeaverDetailsMixin().get_leaver_details(email="")
        self.assertEqual(
            leaver_details["first_name"], self.people_finder_result["first_name"]
        )
        self.assertEqual(
            leaver_details["last_name"], self.people_finder_result["last_name"]
        )
        self.assertEqual(leaver_details["grade"], self.people_finder_result["grade"])
        self.assertEqual(
            leaver_details["personal_phone"],
            self.people_finder_result["primary_phone_number"],
        )
        self.assertEqual(
            leaver_details["work_email"], self.people_finder_result["email"]
        )
        self.assertEqual(
            leaver_details["job_title"],
            self.people_finder_result["roles"][0]["job_title"],
        )
        self.assertEqual(
            leaver_details["team_name"],
            self.people_finder_result["roles"][0]["team"]["name"],
        )

    @mock.patch(
        "leavers.views.leaver.search_people_finder", return_value=[people_finder_result]
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
        "leavers.views.leaver.search_people_finder", return_value=[people_finder_result]
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
        "leavers.views.leaver.search_people_finder", return_value=[people_finder_result]
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

    """
    Tests for `has_required_leaver_details`
    """
