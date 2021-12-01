import uuid
from datetime import date, datetime
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.service_now.interfaces import ServiceNowStubbed
from leavers import factories, models, types
from leavers.views.leaver import LeaverInformationMixin
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


class TestLeaverInformationMixin(TestCase):

    """
    Tests for `get_leaver_information`
    """

    def test_get_leaver_information_new(self):
        LeaverInformationMixin().get_leaver_information(email="joe.bloggs@example.com")

        self.assertEqual(models.LeaverInformation.objects.count(), 1)
        leaver_info = models.LeaverInformation.objects.first()
        self.assertEqual(leaver_info.leaver_email, "joe.bloggs@example.com")

    def test_get_leaver_information_existing(self):
        leaver_info = factories.LeaverInformationFactory(
            leaver_email="joe.bloggs@example.com",
        )

        LeaverInformationMixin().get_leaver_information(email=leaver_info.leaver_email)

        self.assertEqual(models.LeaverInformation.objects.count(), 1)
        leaver_info = models.LeaverInformation.objects.first()
        self.assertEqual(leaver_info.leaver_email, "joe.bloggs@example.com")

    def test_get_leaver_information_other_information(self):
        factories.LeaverInformationFactory.create_batch(5)

        LeaverInformationMixin().get_leaver_information(email="joe.bloggs@example.com")

        self.assertEqual(models.LeaverInformation.objects.count(), 6)
        self.assertEqual(
            models.LeaverInformation.objects.filter(
                leaver_email="joe.bloggs@example.com"
            ).count(),
            1,
        )

    """
    Tests for `get_leaver_details`
    """

    @mock.patch("leavers.views.leaver.search_people_finder", return_value=[])
    def test_get_leaver_details_no_results(self, mock_search_people_finder):
        with self.assertRaisesMessage(Exception, "Issue finding user in People Finder"):
            LeaverInformationMixin().get_leaver_details(email="")

    @mock.patch(
        "leavers.views.leaver.search_people_finder", return_value=[PEOPLE_FINDER_RESULT]
    )
    def test_get_leaver_details_with_result(self, mock_search_people_finder):
        leaver_details = LeaverInformationMixin().get_leaver_details(email="")
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
        leaver_details = LeaverInformationMixin().get_leaver_details(
            email="joe.bloggs@example.com"
        )
        self.assertNotEqual(leaver_details["first_name"], "Joey")

    """
    Tests for `get_leaver_detail_updates`
    """

    def test_get_leaver_detail_updates_no_updates(self):
        leaver_detail_updates = LeaverInformationMixin().get_leaver_detail_updates(
            email="joe.bloggs@example.com"
        )
        self.assertEqual(leaver_detail_updates, {})

    def test_get_leaver_detail_updates_some_updates(self):
        factories.LeaverInformationFactory(
            leaver_email="joe.bloggs@example.com", updates={"first_name": "Joey"}
        )
        leaver_detail_updates = LeaverInformationMixin().get_leaver_detail_updates(
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
        LeaverInformationMixin().store_leaver_detail_updates(
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
        LeaverInformationMixin().store_leaver_detail_updates(
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
        leaver_details = LeaverInformationMixin().get_leaver_details_with_updates(
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
        leaver_details = LeaverInformationMixin().get_leaver_details_with_updates(
            email="joe.bloggs@example.com"
        )
        self.assertEqual(leaver_details["first_name"], "Joey")

    """
    Tests for `store_leaving_date`
    """

    def test_store_leaving_date(self):
        leaver_info = factories.LeaverInformationFactory(
            leaver_email="joe.bloggs@example.com",
        )
        LeaverInformationMixin().store_leaving_date(
            email="joe.bloggs@example.com",
            leaving_date=date(2021, 11, 30),
        )
        leaver_info.refresh_from_db()
        self.assertEqual(
            leaver_info.leaving_date,
            timezone.make_aware(datetime(2021, 11, 30)),
        )

    """
    Tests for `store_correction_information`
    """

    def test_store_correction_information(self):
        leaver_info = factories.LeaverInformationFactory(
            leaver_email="joe.bloggs@example.com"
        )
        LeaverInformationMixin().store_correction_information(
            email="joe.bloggs@example.com",
            information_is_correct=False,
            additional_information="Test additional information",
        )

        leaver_info.refresh_from_db()
        self.assertFalse(leaver_info.information_is_correct)
        self.assertEqual(
            leaver_info.additional_information, "Test additional information"
        )

        LeaverInformationMixin().store_correction_information(
            email="joe.bloggs@example.com",
            information_is_correct=True,
            additional_information="",
        )

        leaver_info.refresh_from_db()
        self.assertTrue(leaver_info.information_is_correct)
        self.assertEqual(leaver_info.additional_information, "")

    """
    Tests for `store_return_option`
    """

    def test_store_return_option_home(self):
        leaver_info = factories.LeaverInformationFactory(
            leaver_email="joe.bloggs@example.com"
        )
        LeaverInformationMixin().store_return_option(
            email="joe.bloggs@example.com", return_option=models.ReturnOption.HOME
        )

        leaver_info.refresh_from_db()
        self.assertEqual(leaver_info.return_option, models.ReturnOption.HOME)

    def test_store_return_option_office(self):
        leaver_info = factories.LeaverInformationFactory(
            leaver_email="joe.bloggs@example.com"
        )
        LeaverInformationMixin().store_return_option(
            email="joe.bloggs@example.com", return_option=models.ReturnOption.OFFICE
        )

        leaver_info.refresh_from_db()
        self.assertEqual(leaver_info.return_option, models.ReturnOption.OFFICE)

    """
    Tests for `store_return_information`
    """

    def test_store_return_information_no_address(self):
        leaver_info = factories.LeaverInformationFactory(
            leaver_email="joe.bloggs@example.com"
        )
        LeaverInformationMixin().store_return_information(
            email="joe.bloggs@example.com",
            personal_phone="0123451234",
            contact_email="joe.bloggs.contact@example.com",
            address=None,
        )

        leaver_info.refresh_from_db()
        self.assertEqual(leaver_info.return_personal_phone, "0123451234")
        self.assertEqual(
            leaver_info.return_contact_email, "joe.bloggs.contact@example.com"
        )

    def test_store_return_information_with_address(self):
        leaver_info = factories.LeaverInformationFactory(
            leaver_email="joe.bloggs@example.com"
        )
        LeaverInformationMixin().store_return_information(
            email="joe.bloggs@example.com",
            personal_phone="0123451234",
            contact_email="joe.bloggs.contact@example.com",
            address="Test address",
        )

        leaver_info.refresh_from_db()
        self.assertEqual(leaver_info.return_personal_phone, "0123451234")
        self.assertEqual(
            leaver_info.return_contact_email, "joe.bloggs.contact@example.com"
        )
        self.assertEqual(leaver_info.return_address, "Test address")


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


class TestKitView(TestCase):
    view_name = "leaver-kit"

    def test_unauthenticated_user(self):
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 302)

    def test_authenticated_user(self):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)

    def initiate_session(self):
        session = self.client.session
        if "assets" not in self.client.session:
            session["assets"] = []
            session.save()
        return session

    def add_kit_to_session(self, asset_name: str, asset_tag: str) -> uuid.UUID:
        session = self.initiate_session()

        asset_uuid = uuid.uuid4()
        session["assets"].append(
            {
                "uuid": str(asset_uuid),
                "tag": asset_tag,
                "name": asset_name,
            }
        )
        session.save()
        return asset_uuid

    @mock.patch("leavers.views.leaver.get_service_now_interface")
    def test_with_assets_in_session(self, mock_get_service_now_interface):
        mock_get_service_now_interface.get_assets_for_user.return_value = []

        user = UserFactory()
        self.client.force_login(user)

        self.add_kit_to_session("Test Asset 1", "Test Tag 1")
        self.add_kit_to_session("Test Asset 2", "Test Tag 2")
        self.add_kit_to_session("Test Asset 3", "Test Tag 3")

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Asset 1")
        self.assertContains(response, "Test Tag 1")
        self.assertContains(response, "Test Asset 2")
        self.assertContains(response, "Test Tag 2")
        self.assertContains(response, "Test Asset 3")
        self.assertContains(response, "Test Tag 3")

    @mock.patch(
        "leavers.views.leaver.get_service_now_interface",
        return_value=ServiceNowStubbed(),
    )
    def test_with_assets_from_service_now(self, mock_get_service_now_interface):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["assets"][0]["name"], "Asset 1")
        self.assertEqual(response.context["assets"][0]["tag"], "1")

    def test_post_no_form_name(self):
        user = UserFactory()
        self.client.force_login(user)

        with self.assertNumQueries(3):
            response = self.client.post(reverse(self.view_name), {})

        self.assertEqual(response.status_code, 200)

    def test_post_add_asset_form(self):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.post(
            reverse(self.view_name),
            {
                "form_name": "add_asset_form",
                "asset_name": "Test Asset",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(self.view_name))

        session_assets = response.client.session["assets"]
        self.assertEqual(len(session_assets), 1)

    @mock.patch(
        "leavers.views.leaver.LeaverInformationMixin.store_correction_information"
    )
    def test_post_correction_form(self, mock_store_correction_information):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.post(
            reverse(self.view_name),
            {
                "form_name": "correction_form",
                "is_correct": "yes",
                "whats_incorrect": "Some additional information",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-return-options"))

        mock_store_correction_information.assert_called_once_with(
            email=user.email,
            information_is_correct=True,
            additional_information="Some additional information",
        )


class TestDeleteKitView(TestCase):
    view_name = "leaver-kit-delete"

    def test_unauthenticated_user(self):
        response = self.client.get(reverse(self.view_name, args=[str(uuid.uuid4())]))

        self.assertEqual(response.status_code, 302)

    def test_authenticated_user(self):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get(reverse(self.view_name, args=[str(uuid.uuid4())]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-kit"))

    def initiate_session(self):
        session = self.client.session
        if "assets" not in self.client.session:
            session["assets"] = []
            session.save()
        return session

    def add_kit_to_session(self, asset_name: str, asset_tag: str) -> uuid.UUID:
        session = self.initiate_session()

        asset_uuid = uuid.uuid4()
        session["assets"].append(
            {
                "uuid": str(asset_uuid),
                "tag": asset_tag,
                "name": asset_name,
            }
        )
        session.save()
        return asset_uuid

    def test_existing_uuid(self):
        user = UserFactory()
        self.client.force_login(user)

        asset_uuid = self.add_kit_to_session("Test Asset 1", "Test Tag 1")

        response = self.client.get(reverse(self.view_name, args=[str(asset_uuid)]))
        session = response.client.session
        session_assets = session["assets"]

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-kit"))
        self.assertEqual(len(session_assets), 0)

    def test_invalid_uuid(self):
        user = UserFactory()
        self.client.force_login(user)

        asset_uuid = self.add_kit_to_session("Test Asset 1", "Test Tag 1")

        response = self.client.get(reverse(self.view_name, args=[str(uuid.uuid4())]))
        session = response.client.session
        session_assets = session["assets"]

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-kit"))
        self.assertEqual(len(session_assets), 1)
        self.assertEqual(session_assets[0]["uuid"], str(asset_uuid))


class TestEquipmentReturnOptionsView(TestCase):
    view_name = "leaver-return-options"

    def test_unauthenticated_user(self):
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 302)

    def test_authenticated_user(self):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)

    @mock.patch("leavers.views.leaver.LeaverInformationMixin.store_return_option")
    def test_post_home(self, mock_store_return_option):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.post(
            reverse(self.view_name),
            {
                "return_option": models.ReturnOption.HOME,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-return-information"))
        mock_store_return_option.assert_called_once_with(
            email=user.email,
            return_option=models.ReturnOption.HOME,
        )

    @mock.patch("leavers.views.leaver.LeaverInformationMixin.store_return_option")
    def test_post_office(self, mock_store_return_option):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.post(
            reverse(self.view_name),
            {
                "return_option": models.ReturnOption.OFFICE,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-return-information"))
        mock_store_return_option.assert_called_once_with(
            email=user.email,
            return_option=models.ReturnOption.OFFICE,
        )

    @mock.patch("leavers.views.leaver.LeaverInformationMixin.store_return_option")
    def test_post_empty(self, mock_store_return_option):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.post(reverse(self.view_name), {})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].errors,
            {"return_option": ["This field is required."]},
        )


class TestEquipmentReturnInformationView(TestCase):
    view_name = "leaver-return-information"

    def test_unauthenticated_user(self):
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 302)

    def test_authenticated_user(self):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)

    def test_home(self):
        user = UserFactory()
        self.client.force_login(user)
        factories.LeaverInformationFactory(
            leaver_email=user.email,
            return_option=models.ReturnOption.HOME,
        )

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        context_form = response.context["form"]
        self.assertTrue(context_form.fields["address"].required)

    def test_office(self):
        user = UserFactory()
        self.client.force_login(user)
        factories.LeaverInformationFactory(
            leaver_email=user.email,
            return_option=models.ReturnOption.OFFICE,
        )

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        context_form = response.context["form"]
        self.assertFalse(context_form.fields["address"].required)

    @mock.patch("leavers.views.leaver.LeaverInformationMixin.store_return_information")
    def test_post(self, mock_store_return_information):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.post(
            reverse(self.view_name),
            {
                "personal_phone": "0123123123",
                "contact_email": "joe.bloggs@example.com",
                "address": "Test Address",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-request-received"))

        mock_store_return_information.assert_called_once_with(
            email=user.email,
            personal_phone="0123123123",
            contact_email="joe.bloggs@example.com",
            address="Test Address",
        )
