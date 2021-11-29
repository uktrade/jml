from datetime import date
from unittest import mock
from unittest.case import skip

from django.test import TestCase
from django.urls import reverse
from django.urls.base import resolve

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
            leaver_details["directorate"],
            PEOPLE_FINDER_RESULT["roles"][0]["team"]["name"],
        )

    @mock.patch(
        "leavers.views.leaver.search_people_finder", return_value=[PEOPLE_FINDER_RESULT]
    )
    def test_get_leaver_details_existing_updates(self, mock_search_people_finder):
        factories.LeaverInformationFactory(
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
        factories.LeaverInformationFactory(
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
            models.LeaverInformation.objects.filter(
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

        leaver_updates = models.LeaverInformation.objects.get(
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
        factories.LeaverInformationFactory(
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
                "directorate": "Example Team",
                "first_name": "Joe",
                "grade": "Example Grade",
                "job_title": "Example Job Title",
                "last_name": "Bloggs",
                "manager": "",
                "staff_id": "",
                "personal_address": "",
                "personal_email": "",
                "personal_phone": "0987654321",
                "photo": "",
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
            "staff_id": "Updated Staff ID",
            "personal_address": "Updated Address",
            "personal_email": "Updated Personal Email",
            "personal_phone": "Updated Number",
            "work_email": "Updated Work Email",
        }
        factories.LeaverInformationFactory(leaver_email=user.email, updates=updates)
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
                "staff_id": updates["staff_id"],
                "personal_address": updates["personal_address"],
                "personal_email": updates["personal_email"],
                "personal_phone": updates["personal_phone"],
                "work_email": updates["work_email"],
            },
        )

    def test_submit_missing_required_data(self, mock_search_people_finder):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.post(reverse(self.view_name), {})

        self.assertEqual(response.status_code, 200)

    def test_submit_contains_required_data(self, mock_search_people_finder):
        user = UserFactory()
        updates: types.LeaverDetailUpdates = {
            "department": "Updated Department",
            "directorate": "Updated Directorate",
            "first_name": "UpdatedFirstName",
            "grade": "Updated Grade",
            "job_title": "Updated Job Title",
            "last_name": "UpdatedLastName",
            "manager": "Updated Manager",
            "staff_id": "Updated Staff ID",
            "personal_address": "Updated Address",
            "personal_email": "new.personal.email@example.com",
            "personal_phone": "Updated Number",
            "work_email": "new.work.email@example.com",
        }
        factories.LeaverInformationFactory(leaver_email=user.email, updates=updates)
        self.client.force_login(user)

        response = self.client.post(reverse(self.view_name), {})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-kit"))


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
                "directorate": "Example Team",
                "first_name": "Joe",
                "grade": "Example Grade",
                "job_title": "Example Job Title",
                "last_name": "Bloggs",
                "manager": "",
                "staff_id": "",
                "personal_address": "",
                "personal_email": "",
                "personal_phone": "0987654321",
                "photo": "",
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
            "staff_id": "Updated Staff ID",
            "personal_address": "Updated Address",
            "personal_email": "Updated Personal Email",
            "personal_phone": "Updated Number",
            "work_email": "Updated Work Email",
        }
        factories.LeaverInformationFactory(leaver_email=user.email, updates=updates)
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
                "staff_id": updates["staff_id"],
                "personal_address": updates["personal_address"],
                "personal_email": updates["personal_email"],
                "personal_phone": updates["personal_phone"],
                "work_email": updates["work_email"],
            },
        )

    def test_submit_missing_required_data(self, mock_search_people_finder):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.post(
            reverse(self.view_name),
            {
                "department": "",
                "directorate": "",
                "first_name": "",
                "grade": "",
                "job_title": "",
                "last_name": "",
                "manager": "",
                "staff_id": "",
                "personal_address": "",
                "personal_email": "",
                "personal_phone": "",
                "work_email": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, "form", "department", "This field is required.")
        self.assertFormError(response, "form", "directorate", "This field is required.")
        self.assertFormError(response, "form", "first_name", "This field is required.")
        self.assertFormError(response, "form", "grade", "This field is required.")
        self.assertFormError(response, "form", "job_title", "This field is required.")
        self.assertFormError(response, "form", "last_name", "This field is required.")
        self.assertFormError(response, "form", "manager", "This field is required.")
        self.assertFormError(response, "form", "staff_id", "This field is required.")
        self.assertFormError(
            response, "form", "personal_address", "This field is required."
        )
        self.assertFormError(
            response, "form", "personal_email", "This field is required."
        )

    def test_submit_contains_required_data(self, mock_search_people_finder):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.post(
            reverse(self.view_name),
            {
                "department": "Test Department",
                "directorate": "Test Directorate",
                "first_name": "FirstName",
                "grade": "Grade",
                "job_title": "Job Title",
                "last_name": "LastName",
                "manager": "Manager Name",
                "staff_id": "Staff ID",
                "personal_address": "Personal Address",
                "personal_email": "someone@example.com",
                "personal_phone": "0123456789",
                "work_email": user.email,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-confirm-details"))

        leaver_updates_obj = models.LeaverInformation.objects.get(
            leaver_email=user.email
        )
        leaver_updates: types.LeaverDetailUpdates = leaver_updates_obj.updates

        self.assertEqual(leaver_updates["department"], "Test Department")
        self.assertEqual(leaver_updates["directorate"], "Test Directorate")
        self.assertEqual(leaver_updates["first_name"], "FirstName")
        self.assertEqual(leaver_updates["grade"], "Grade")
        self.assertEqual(leaver_updates["job_title"], "Job Title")
        self.assertEqual(leaver_updates["last_name"], "LastName")
        self.assertEqual(leaver_updates["manager"], "Manager Name")
        self.assertEqual(leaver_updates["staff_id"], "Staff ID")
        self.assertEqual(leaver_updates["personal_address"], "Personal Address")
        self.assertEqual(leaver_updates["personal_email"], "someone@example.com")
        self.assertEqual(leaver_updates["personal_phone"], "0123456789")
        self.assertEqual(leaver_updates["work_email"], user.email)
