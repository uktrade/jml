import uuid
from datetime import date, datetime
from typing import List, cast
from unittest import mock

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from activity_stream.factories import ActivityStreamStaffSSOUserFactory
from core.service_now.interfaces import ServiceNowStubbed
from core.utils.staff_index import StaffDocument
from leavers import factories, models, types
from leavers.forms.leaver import ReturnOptions, StaffType
from leavers.views.leaver import LeaverInformationMixin
from user.test.factories import UserFactory

STAFF_DOCUMENT = StaffDocument.from_dict(
    {
        "uuid": "",
        "staff_sso_activity_stream_id": "1",
        "staff_sso_legacy_id": "123",
        "staff_sso_contact_email_address": "",
        "staff_sso_email_address": "joe.bloggs@example.com",  # /PS-IGNORE
        "staff_sso_first_name": "Joe",  # /PS-IGNORE
        "staff_sso_last_name": "Bloggs",
        "people_finder_directorate": "",
        "people_finder_first_name": "Joe",  # /PS-IGNORE
        "people_finder_grade": "Example Grade",
        "people_finder_image": "",
        "people_finder_job_title": "Job title",
        "people_finder_last_name": "Bloggs",
        "people_finder_phone": "0123456789",
        "people_finder_email": "joe.bloggs@example.com",  # /PS-IGNORE
        "people_finder_photo": "",
        "people_finder_photo_small": "",
        "service_now_user_id": "",
        "service_now_department_id": settings.SERVICE_NOW_DIT_DEPARTMENT_SYS_ID,
        "service_now_department_name": "Department of International Trade",
        "service_now_directorate_id": "",
        "service_now_directorate_name": "",
        "people_data_employee_number": "12345",
    }
)
STAFF_INDEX_RETURN_VALUE: List[StaffDocument] = [STAFF_DOCUMENT]


@mock.patch(
    "leavers.views.leaver.search_staff_index",
    return_value=STAFF_INDEX_RETURN_VALUE,
)
class TestLeaverInformationMixin(TestCase):

    """
    Tests for `get_leaver_information`
    """

    def setUp(self) -> None:
        self.leaver_email = "joe.bloggs@example.com"  # /PS-IGNORE
        self.leaver_activity_stream_user = ActivityStreamStaffSSOUserFactory(
            email_address=self.leaver_email
        )

    def test_get_leaver_information_new(self, mock_get_search_results) -> None:

        LeaverInformationMixin().get_leaver_information(
            email=self.leaver_email,
            requester=UserFactory(),
        )

        self.assertEqual(models.LeaverInformation.objects.count(), 1)
        leaver_info_obj = cast(
            models.LeaverInformation, models.LeaverInformation.objects.first()
        )

        self.assertEqual(leaver_info_obj.leaver_email, self.leaver_email)

    def test_get_leaver_information_existing(self, mock_get_search_results) -> None:
        leaver_info = factories.LeaverInformationFactory(
            leaver_email=self.leaver_email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
        )

        LeaverInformationMixin().get_leaver_information(
            email=leaver_info.leaver_email, requester=UserFactory()
        )

        self.assertEqual(models.LeaverInformation.objects.count(), 1)

        leaver_info_obj = cast(
            models.LeaverInformation, models.LeaverInformation.objects.first()
        )

        self.assertTrue(leaver_info_obj)
        self.assertEqual(leaver_info_obj.leaver_email, self.leaver_email)

    def test_get_leaver_information_other_information(
        self, mock_get_search_results
    ) -> None:
        factories.LeaverInformationFactory.create_batch(5)

        LeaverInformationMixin().get_leaver_information(
            email=self.leaver_email,
            requester=UserFactory(),
        )

        self.assertEqual(models.LeaverInformation.objects.count(), 6)
        self.assertEqual(
            models.LeaverInformation.objects.filter(
                leaver_email=self.leaver_email,
            ).count(),
            1,
        )

    """
    Tests for `get_leaver_details`
    """

    def test_get_leaver_details_no_results(self, mock_get_search_results) -> None:
        mock_get_search_results.return_value = []
        with self.assertRaisesMessage(
            Exception, "Unable to find leaver in the Staff Index."
        ):
            LeaverInformationMixin().get_leaver_details(email="")

    def test_get_leaver_details_with_result(self, mock_get_search_results) -> None:
        leaver_details = LeaverInformationMixin().get_leaver_details(
            email=self.leaver_email
        )
        self.assertEqual(leaver_details["first_name"], "Joe")  # /PS-IGNORE
        self.assertEqual(leaver_details["last_name"], "Bloggs")
        self.assertEqual(leaver_details["job_title"], "Job title")
        self.assertEqual(leaver_details["directorate"], "")

    def test_get_leaver_details_existing_updates(self, mock_get_search_results) -> None:
        factories.LeaverInformationFactory(
            leaver_email=self.leaver_email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
            updates={"first_name": "Joey"},  # /PS-IGNORE
        )

        leaver_details = LeaverInformationMixin().get_leaver_details(
            email=self.leaver_email,
        )
        self.assertNotEqual(leaver_details["first_name"], "Joey")  # /PS-IGNORE

    """
    Tests for `get_leaver_detail_updates`
    """

    def test_get_leaver_detail_updates_no_updates(
        self, mock_get_search_results
    ) -> None:
        leaver_detail_updates = LeaverInformationMixin().get_leaver_detail_updates(
            email=self.leaver_email,
            requester=UserFactory(),
        )
        self.assertEqual(leaver_detail_updates, {})

    def test_get_leaver_detail_updates_some_updates(
        self, mock_get_search_results
    ) -> None:

        factories.LeaverInformationFactory(
            leaver_email=self.leaver_email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
            updates={"first_name": "Joey"},  # /PS-IGNORE
        )

        leaver_detail_updates = LeaverInformationMixin().get_leaver_detail_updates(
            email=self.leaver_email,
            requester=UserFactory(),
        )
        self.assertEqual(leaver_detail_updates, {"first_name": "Joey"})  # /PS-IGNORE

    """
    Tests for `store_leaver_detail_updates`
    """

    def store_leaver_detail_updates_no_changes(self, mock_get_search_results) -> None:
        LeaverInformationMixin().store_leaver_detail_updates(
            email=self.leaver_email,
            requester=UserFactory(),
            updates={},
        )
        self.assertEqual(
            models.LeaverInformation.objects.filter(
                leaver_email=self.leaver_email,
            ).count(),
            1,
        )

    def store_leaver_detail_updates_some_changes(self, mock_get_search_results) -> None:
        LeaverInformationMixin().store_leaver_detail_updates(
            email=self.leaver_email,
            requester=UserFactory(),
            updates={"first_name": "Joey"},  # /PS-IGNORE
        )

        leaver_updates = models.LeaverInformation.objects.get(
            leaver_email=self.leaver_email,
        )
        self.assertEqual(leaver_updates.updates, {"first_name": "Joey"})  # /PS-IGNORE

    """
    Tests for `get_leaver_details_with_updates`
    """

    def test_get_leaver_details_with_updates_no_updates(
        self, mock_get_search_results
    ) -> None:
        leaver_details = LeaverInformationMixin().get_leaver_details_with_updates(
            email=self.leaver_email,
            requester=UserFactory(),
        )
        self.assertEqual(leaver_details["first_name"], "Joe")  # /PS-IGNORE

    def test_get_leaver_details_with_updates_some_updates(
        self, mock_get_search_results
    ) -> None:
        factories.LeaverInformationFactory(
            leaver_email=self.leaver_email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
            updates={"first_name": "Joey"},  # /PS-IGNORE
        )
        leaver_details = LeaverInformationMixin().get_leaver_details_with_updates(
            email=self.leaver_email,
            requester=UserFactory(),
        )
        self.assertEqual(leaver_details["first_name"], "Joey")  # /PS-IGNORE

    """
    Tests for `store_leaving_dates`
    """

    def test_store_leaving_dates(self, mock_get_search_results) -> None:
        leaver_info = factories.LeaverInformationFactory(
            leaver_email=self.leaver_email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
        )
        LeaverInformationMixin().store_leaving_dates(
            email=self.leaver_email,
            requester=UserFactory(),
            last_day=date(2021, 11, 15),
            leaving_date=date(2021, 11, 30),
        )
        leaver_info.refresh_from_db()
        self.assertEqual(
            leaver_info.last_day,
            timezone.make_aware(datetime(2021, 11, 15)),
        )
        self.assertEqual(
            leaver_info.leaving_date,
            timezone.make_aware(datetime(2021, 11, 30)),
        )

    """
    Tests for `store_cirrus_kit_information`
    """

    def test_store_cirrus_kit_information(self, mock_get_search_results) -> None:
        leaver_info = factories.LeaverInformationFactory(
            leaver_email=self.leaver_email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
        )
        LeaverInformationMixin().store_cirrus_kit_information(
            email=self.leaver_email,
            requester=UserFactory(),
            cirrus_assets=[],
            information_is_correct=False,
            additional_information="Test additional information",
        )

        leaver_info.refresh_from_db()
        self.assertFalse(leaver_info.information_is_correct)
        self.assertEqual(
            leaver_info.additional_information, "Test additional information"
        )

        LeaverInformationMixin().store_cirrus_kit_information(
            email=self.leaver_email,
            requester=UserFactory(),
            cirrus_assets=[],
            information_is_correct=True,
            additional_information="",
        )

        leaver_info.refresh_from_db()
        self.assertTrue(leaver_info.information_is_correct)
        self.assertEqual(leaver_info.additional_information, "")

    """
    Tests for `store_return_option`
    """

    def test_store_return_option_home(self, mock_get_search_results) -> None:
        leaver_info = factories.LeaverInformationFactory(
            leaver_email=self.leaver_email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
        )

        LeaverInformationMixin().store_return_option(
            email=self.leaver_email,
            requester=UserFactory(),
            return_option=ReturnOptions.HOME.value,
        )

        leaver_info.refresh_from_db()
        self.assertEqual(leaver_info.return_option, ReturnOptions.HOME.value)

    def test_store_return_option_office(self, mock_get_search_results) -> None:
        leaver_info = factories.LeaverInformationFactory(
            leaver_email=self.leaver_email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
        )

        LeaverInformationMixin().store_return_option(
            email=self.leaver_email,
            requester=UserFactory(),
            return_option=ReturnOptions.OFFICE.value,
        )

        leaver_info.refresh_from_db()
        self.assertEqual(leaver_info.return_option, ReturnOptions.OFFICE.value)

    """
    Tests for `store_return_information`
    """

    def test_store_return_information_no_address(self, mock_get_search_results) -> None:
        leaver_info = factories.LeaverInformationFactory(
            leaver_email=self.leaver_email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
        )
        LeaverInformationMixin().store_return_information(
            email=self.leaver_email,
            requester=UserFactory(),
            personal_phone="0123451234",
            contact_email=self.leaver_email,
            address=None,
        )

        leaver_info.refresh_from_db()
        self.assertEqual(leaver_info.return_personal_phone, "0123451234")
        self.assertEqual(
            leaver_info.return_contact_email,
            self.leaver_email,
        )

    def test_store_return_information_with_address(
        self, mock_get_search_results
    ) -> None:
        leaver_info = factories.LeaverInformationFactory(
            leaver_email=self.leaver_email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
        )
        LeaverInformationMixin().store_return_information(
            email=self.leaver_email,
            requester=UserFactory(),
            personal_phone="0123451234",
            contact_email=self.leaver_email,
            address={
                "building_and_street": "Example Building name",
                "city": "Bristol",
                "county": "Bristol",
                "postcode": "AB1 2CD",  # /PS-IGNORE
            },
        )

        leaver_info.refresh_from_db()
        self.assertEqual(leaver_info.return_personal_phone, "0123451234")
        self.assertEqual(
            leaver_info.return_contact_email,
            self.leaver_email,
        )
        self.assertEqual(
            leaver_info.return_address_building_and_street,
            "Example Building name",
        )
        self.assertEqual(leaver_info.return_address_city, "Bristol")
        self.assertEqual(leaver_info.return_address_county, "Bristol")
        self.assertEqual(leaver_info.return_address_postcode, "AB1 2CD")  # /PS-IGNORE


@mock.patch(
    "leavers.views.leaver.search_staff_index",
    return_value=STAFF_INDEX_RETURN_VALUE,
)
class TestConfirmDetailsView(TestCase):
    view_name = "leaver-confirm-details"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_user = ActivityStreamStaffSSOUserFactory(
            email_address=self.leaver.email,
        )

    def test_unauthenticated_user(self, mock_get_search_results) -> None:
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 302)

    def test_authenticated_user(self, mock_get_search_results) -> None:
        self.client.force_login(self.leaver)
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Confirm your information")

        leaver_details: types.LeaverDetails = response.context["leaver_details"]
        self.assertEqual(leaver_details["directorate"], "")
        self.assertEqual(leaver_details["first_name"], "Joe")  # /PS-IGNORE
        self.assertEqual(leaver_details["job_title"], "Job title")
        self.assertEqual(leaver_details["last_name"], "Bloggs")
        self.assertEqual(leaver_details["staff_id"], "12345")
        self.assertEqual(leaver_details["contact_email_address"], "")
        self.assertEqual(leaver_details["photo"], "")

    @mock.patch(
        "leavers.views.leaver.get_staff_document_from_staff_index",
        return_value=STAFF_DOCUMENT,
    )
    def test_existing_updates(
        self, mock_get_staff_document_from_staff_index, mock_get_search_results
    ) -> None:
        updates: types.LeaverDetailUpdates = {
            "directorate": "2",
            "first_name": "UpdatedFirstName",  # /PS-IGNORE
            "job_title": "Updated Job Title",
            "last_name": "UpdatedLastName",  # /PS-IGNORE
            "contact_email_address": "Updated Personal Email",
        }
        factories.LeaverInformationFactory(
            leaver_email=self.leaver.email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
            updates=updates,
        )
        self.client.force_login(self.leaver)
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Confirm your information")
        self.assertEqual(
            response.context["leaver_details"],
            {
                "first_name": updates["first_name"],
                "last_name": updates["last_name"],
                "staff_id": "12345",
                "contact_email_address": updates["contact_email_address"],
                "job_title": updates["job_title"],
                "directorate": "Directorate 2",
                "photo": "",
            },
        )

    def test_submit_missing_required_data(self, mock_get_search_results) -> None:
        self.client.force_login(self.leaver)

        response = self.client.post(reverse(self.view_name), {})

        self.assertEqual(response.status_code, 200)

    @mock.patch(
        "leavers.views.leaver.get_staff_document_from_staff_index",
        return_value=STAFF_DOCUMENT,
    )
    def test_submit_contains_required_data(
        self, mock_get_staff_document_from_staff_index, mock_get_search_results
    ) -> None:
        updates: types.LeaverDetailUpdates = {
            "directorate": "1",
            "first_name": "UpdatedFirstName",  # /PS-IGNORE
            "job_title": "Updated Job Title",
            "last_name": "UpdatedLastName",  # /PS-IGNORE
            "contact_email_address": "new.personal.email@example.com",  # /PS-IGNORE
        }
        factories.LeaverInformationFactory(
            leaver_email=self.leaver.email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
            leaving_request__security_clearance="sc",
            leaving_request__is_rosa_user=True,
            leaving_request__holds_government_procurement_card=True,
            updates=updates,
            has_locker=True,
            has_dse=True,
        )
        self.client.force_login(self.leaver)

        response = self.client.post(
            reverse(self.view_name),
            {},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-request-received"))


@mock.patch(
    "leavers.views.leaver.search_staff_index",
    return_value=STAFF_INDEX_RETURN_VALUE,
)
class TestUpdateDetailsView(TestCase):
    view_name = "leaver-update-details"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_user = ActivityStreamStaffSSOUserFactory(
            email_address=self.leaver.email,
        )

    def test_unauthenticated_user(self, mock_get_search_results) -> None:
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 302)

    def test_authenticated_user(self, mock_get_search_results) -> None:
        self.client.force_login(self.leaver)

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hi Joe Bloggs,")  # /PS-IGNORE
        self.assertContains(
            response, "Please check, update and add any missing information."
        )

        form = response.context["form"]
        self.assertEqual(form.initial["directorate"], "")
        self.assertEqual(form.initial["first_name"], "Joe")  # /PS-IGNORE
        self.assertEqual(form.initial["job_title"], "Job title")
        self.assertEqual(form.initial["last_name"], "Bloggs")  # /PS-IGNORE
        self.assertEqual(form.initial["contact_email_address"], "")
        self.assertEqual(form.initial["photo"], "")

    def test_existing_updates(self, mock_get_search_results) -> None:
        updates: types.LeaverDetailUpdates = {
            "directorate": "2",
            "first_name": "UpdatedFirstName",  # /PS-IGNORE
            "job_title": "Updated Job Title",
            "last_name": "UpdatedLastName",  # /PS-IGNORE
            "contact_email_address": "Updated Personal Email",
        }
        factories.LeaverInformationFactory(
            leaver_email=self.leaver.email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
            updates=updates,
        )
        self.client.force_login(self.leaver)

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Hi UpdatedFirstName UpdatedLastName,",  # /PS-IGNORE
        )
        self.assertContains(
            response, "Please check, update and add any missing information."
        )

        form = response.context["form"]
        self.assertEqual(
            form.initial,
            {
                "photo": "",
                "directorate": updates["directorate"],
                "first_name": updates["first_name"],
                "job_title": updates["job_title"],
                "last_name": updates["last_name"],
                "contact_email_address": updates["contact_email_address"],
                "has_dse": None,
                "has_gov_procurement_card": None,
                "has_rosa_kit": None,
                "security_clearance": None,
                "has_locker": None,
                "last_day": None,
                "leaving_date": None,
                "staff_id": "12345",
                "staff_type": None,
            },
        )

    def test_submit_missing_required_data(self, mock_get_search_results) -> None:
        self.client.force_login(self.leaver)

        response = self.client.post(
            reverse(self.view_name),
            {
                "directorate": "",
                "first_name": "",
                "job_title": "",
                "last_name": "",
                "contact_email_address": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, "form", "directorate", "This field is required.")
        self.assertFormError(response, "form", "first_name", "This field is required.")
        self.assertFormError(response, "form", "job_title", "This field is required.")
        self.assertFormError(response, "form", "last_name", "This field is required.")
        self.assertFormError(
            response, "form", "contact_email_address", "This field is required."
        )

    def test_submit_contains_required_data(self, mock_get_search_results) -> None:
        self.client.force_login(self.leaver)

        response = self.client.post(
            reverse(self.view_name),
            {
                "first_name": "FirstName",  # /PS-IGNORE
                "last_name": "LastName",  # /PS-IGNORE
                "contact_email_address": "someone@example.com",  # /PS-IGNORE
                "job_title": "Job Title",
                "directorate": "1",
                "security_clearance": "sc",
                "has_locker": "yes",
                "has_gov_procurement_card": "yes",
                "has_rosa_kit": "yes",
                "has_dse": "yes",
                "leaving_date_0": 30,
                "leaving_date_1": 12,
                "leaving_date_2": 2022,
                "last_day_0": 15,
                "last_day_1": 12,
                "last_day_2": 2022,
                "staff_type": StaffType.CONTRACTOR.value,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-cirrus-equipment"))

        leaver_updates_obj = models.LeaverInformation.objects.get(
            leaver_email=self.leaver.email,
        )
        leaver_updates: types.LeaverDetailUpdates = leaver_updates_obj.updates

        self.assertEqual(leaver_updates["directorate"], "1")
        self.assertEqual(leaver_updates["first_name"], "FirstName")  # /PS-IGNORE
        self.assertEqual(leaver_updates["job_title"], "Job Title")
        self.assertEqual(leaver_updates["last_name"], "LastName")  # /PS-IGNORE

        self.assertEqual(
            leaver_updates["contact_email_address"],
            "someone@example.com",  # /PS-IGNORE
        )


class TestCirrusEquipmentView(TestCase):
    view_name = "leaver-cirrus-equipment"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_staff_sso = ActivityStreamStaffSSOUserFactory(
            email_address=self.leaver.email,
        )
        self.leaver_information = factories.LeaverInformationFactory(
            leaver_email=self.leaver.email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_staff_sso,
            leaving_request__user_requesting=self.leaver,
        )

    def test_unauthenticated_user(self) -> None:
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 302)

    def test_authenticated_user(self) -> None:
        self.client.force_login(self.leaver)

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)

    def initiate_session(self) -> SessionBase:
        session = self.client.session
        if "cirrus_assets" not in self.client.session:
            session["cirrus_assets"] = []
            session.save()
        return session

    def add_kit_to_session(self, asset_name: str, asset_tag: str) -> uuid.UUID:
        session = self.initiate_session()

        asset_uuid = uuid.uuid4()
        session["cirrus_assets"].append(
            {
                "uuid": str(asset_uuid),
                "tag": asset_tag,
                "name": asset_name,
            }
        )
        session.save()
        return asset_uuid

    @mock.patch("leavers.views.leaver.get_service_now_interface")
    def test_with_assets_in_session(self, mock_get_service_now_interface) -> None:
        mock_get_service_now_interface.get_assets_for_user.return_value = []

        self.client.force_login(self.leaver)

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
    def test_with_assets_from_service_now(self, mock_get_service_now_interface) -> None:
        self.client.force_login(self.leaver)

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["cirrus_assets"][0]["name"], "Asset 1")
        self.assertEqual(response.context["cirrus_assets"][0]["tag"], "1")

    def test_post_no_form_name(self) -> None:
        self.client.force_login(self.leaver)

        with self.assertNumQueries(16):
            response = self.client.post(reverse(self.view_name), {})

        self.assertEqual(response.status_code, 200)

    def test_post_add_asset_form(self) -> None:
        self.client.force_login(self.leaver)

        with self.assertNumQueries(19):
            response = self.client.post(
                reverse(self.view_name),
                {
                    "form_name": "add_asset_form",
                    "asset_name": "Test Asset",
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(self.view_name))

        session_assets = response.client.session["cirrus_assets"]
        self.assertEqual(len(session_assets), 1)

    @mock.patch(
        "leavers.views.leaver.LeaverInformationMixin.store_cirrus_kit_information"
    )
    def test_post_correction_form(self, mock_store_cirrus_kit_information) -> None:
        self.client.force_login(self.leaver)

        with self.assertNumQueries(13):
            response = self.client.post(
                reverse(self.view_name),
                {
                    "form_name": "correction_form",
                    "is_correct": "no",
                    "whats_incorrect": "Some additional information",
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-return-options"))

        mock_store_cirrus_kit_information.assert_called_once_with(
            email=self.leaver.email,
            requester=self.leaver,
            information_is_correct=False,
            additional_information="Some additional information",
            cirrus_assets=[],
        )


class TestDisplayScreenEquipmentView(TestCase):
    view_name = "leaver-display-screen-equipment"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_staff_sso = ActivityStreamStaffSSOUserFactory(
            email_address=self.leaver.email,
        )
        self.leaver_information = factories.LeaverInformationFactory(
            leaver_email=self.leaver.email,
            has_dse=True,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_staff_sso,
            leaving_request__user_requesting=self.leaver,
        )

    def test_unauthenticated_user(self) -> None:
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 302)

    def test_authenticated_user(self) -> None:
        self.leaver_information.has_dse = False
        self.leaver_information.save()

        self.client.force_login(self.leaver)

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-confirm-details"))

    def test_no_dse(self) -> None:
        self.client.force_login(self.leaver)

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)

    def initiate_session(self) -> SessionBase:
        session = self.client.session
        if "dse_assets" not in self.client.session:
            session["dse_assets"] = []
            session.save()
        return session

    def add_kit_to_session(self, asset_name: str) -> uuid.UUID:
        session = self.initiate_session()

        asset_uuid = uuid.uuid4()
        session["dse_assets"].append(
            {
                "uuid": str(asset_uuid),
                "name": asset_name,
            }
        )
        session.save()
        return asset_uuid

    @mock.patch("leavers.views.leaver.get_service_now_interface")
    def test_with_assets_in_session(self, mock_get_service_now_interface) -> None:
        mock_get_service_now_interface.get_assets_for_user.return_value = []

        self.client.force_login(self.leaver)

        self.add_kit_to_session("Test Asset 1")
        self.add_kit_to_session("Test Asset 2")
        self.add_kit_to_session("Test Asset 3")

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Asset 1")
        self.assertContains(response, "Test Asset 2")
        self.assertContains(response, "Test Asset 3")

    def test_post_no_form_name(self) -> None:
        self.client.force_login(self.leaver)

        with self.assertNumQueries(11):
            response = self.client.post(reverse(self.view_name), {})

        self.assertEqual(response.status_code, 200)

    def test_post_add_asset_form(self) -> None:
        self.client.force_login(self.leaver)

        with self.assertNumQueries(14):
            response = self.client.post(
                reverse(self.view_name),
                {
                    "form_name": "add_asset_form",
                    "asset_name": "Test Asset",
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(self.view_name))

        session_assets = response.client.session["dse_assets"]
        self.assertEqual(len(session_assets), 1)

    @mock.patch(
        "leavers.views.leaver.LeaverInformationMixin.store_display_screen_equipment"
    )
    def test_post_submission_form(self, mock_store_display_screen_equipment) -> None:
        self.client.force_login(self.leaver)

        with self.assertNumQueries(8):
            response = self.client.post(
                reverse(self.view_name),
                {
                    "form_name": "submission_form",
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-confirm-details"))

        mock_store_display_screen_equipment.assert_called_once_with(
            email=self.leaver.email,
            requester=self.leaver,
            dse_assets=[],
        )


class TestDeleteCirrusEquipmentView(TestCase):
    view_name = "leaver-cirrus-equipment-delete"

    def test_unauthenticated_user(self) -> None:
        response = self.client.get(reverse(self.view_name, args=[str(uuid.uuid4())]))

        self.assertEqual(response.status_code, 302)

    def test_authenticated_user(self) -> None:
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get(reverse(self.view_name, args=[str(uuid.uuid4())]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-cirrus-equipment"))

    def initiate_session(self) -> SessionBase:
        session = self.client.session
        if "cirrus_assets" not in self.client.session:
            session["cirrus_assets"] = []
            session.save()
        return session

    def add_kit_to_session(self, asset_name: str, asset_tag: str) -> uuid.UUID:
        session = self.initiate_session()

        asset_uuid = uuid.uuid4()
        session["cirrus_assets"].append(
            {
                "uuid": str(asset_uuid),
                "tag": asset_tag,
                "name": asset_name,
            }
        )
        session.save()
        return asset_uuid

    def test_existing_uuid(self) -> None:
        user = UserFactory()
        self.client.force_login(user)

        asset_uuid = self.add_kit_to_session("Test Asset 1", "Test Tag 1")

        response = self.client.get(reverse(self.view_name, args=[str(asset_uuid)]))
        session = response.client.session
        session_assets = session["cirrus_assets"]

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-cirrus-equipment"))
        self.assertEqual(len(session_assets), 0)

    def test_invalid_uuid(self) -> None:
        user = UserFactory()
        self.client.force_login(user)

        asset_uuid = self.add_kit_to_session("Test Asset 1", "Test Tag 1")

        response = self.client.get(reverse(self.view_name, args=[str(uuid.uuid4())]))
        session = response.client.session
        session_assets = session["cirrus_assets"]

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-cirrus-equipment"))
        self.assertEqual(len(session_assets), 1)
        self.assertEqual(session_assets[0]["uuid"], str(asset_uuid))


class TestCirrusEquipmentReturnOptionsView(TestCase):
    view_name = "leaver-return-options"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_staff_sso = ActivityStreamStaffSSOUserFactory(
            email_address=self.leaver.email,
        )
        self.leaver_information = factories.LeaverInformationFactory(
            leaver_email=self.leaver.email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_staff_sso,
            leaving_request__user_requesting=self.leaver,
        )

    def test_unauthenticated_user(self) -> None:
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 302)

    def test_authenticated_user(self) -> None:
        self.client.force_login(self.leaver)

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)

    @mock.patch("leavers.views.leaver.LeaverInformationMixin.store_return_option")
    def test_post_home(self, mock_store_return_option) -> None:
        self.client.force_login(self.leaver)

        response = self.client.post(
            reverse(self.view_name),
            {
                "return_option": ReturnOptions.HOME.value,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-return-information"))
        mock_store_return_option.assert_called_once_with(
            email=self.leaver.email,
            requester=self.leaver,
            return_option=ReturnOptions.HOME.value,
        )

    @mock.patch("leavers.views.leaver.LeaverInformationMixin.store_return_option")
    def test_post_office(self, mock_store_return_option) -> None:
        self.client.force_login(self.leaver)

        response = self.client.post(
            reverse(self.view_name),
            {
                "return_option": ReturnOptions.OFFICE.value,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-return-information"))
        mock_store_return_option.assert_called_once_with(
            email=self.leaver.email,
            requester=self.leaver,
            return_option=ReturnOptions.OFFICE.value,
        )

    @mock.patch("leavers.views.leaver.LeaverInformationMixin.store_return_option")
    def test_post_empty(self, mock_store_return_option) -> None:
        self.client.force_login(self.leaver)

        response = self.client.post(reverse(self.view_name), {})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].errors,
            {"return_option": ["This field is required."]},
        )


class TestCirrusEquipmentReturnInformationView(TestCase):
    view_name = "leaver-return-information"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_user = ActivityStreamStaffSSOUserFactory(
            email_address=self.leaver.email,
        )

    def test_unauthenticated_user(self) -> None:
        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 302)

    def test_authenticated_user(self) -> None:
        self.client.force_login(self.leaver)

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)

    def test_home(self) -> None:
        self.client.force_login(self.leaver)
        factories.LeaverInformationFactory(
            leaver_email=self.leaver.email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
            return_option=ReturnOptions.HOME.value,
        )

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        context_form = response.context["form"]
        self.assertTrue(context_form.fields["address_building"].required)
        self.assertTrue(context_form.fields["address_city"].required)
        self.assertTrue(context_form.fields["address_county"].required)
        self.assertTrue(context_form.fields["address_postcode"].required)

    def test_office(self) -> None:
        self.client.force_login(self.leaver)
        factories.LeaverInformationFactory(
            leaver_email=self.leaver.email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
            return_option=ReturnOptions.OFFICE.value,
        )

        response = self.client.get(reverse(self.view_name))

        self.assertEqual(response.status_code, 200)
        context_form = response.context["form"]
        self.assertFalse(context_form.fields["address_building"].required)
        self.assertFalse(context_form.fields["address_city"].required)
        self.assertFalse(context_form.fields["address_county"].required)
        self.assertFalse(context_form.fields["address_postcode"].required)

    @mock.patch("leavers.views.leaver.LeaverInformationMixin.store_return_information")
    def test_post(self, mock_store_return_information) -> None:
        self.client.force_login(self.leaver)
        factories.LeaverInformationFactory(
            leaver_email=self.leaver.email,
            leaving_request__leaver_activitystream_user=self.leaver_activity_stream_user,
            return_option=ReturnOptions.HOME.value,
        )

        response = self.client.post(
            reverse(self.view_name),
            {
                "personal_phone": "0123123123",  # /PS-IGNORE
                "contact_email": "joe.bloggs@example.com",  # /PS-IGNORE
                "address_building": "Example Building name",  # /PS-IGNORE
                "address_city": "Bristol",
                "address_county": "Bristol",
                "address_postcode": "AB1 2CD",  # /PS-IGNORE
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-display-screen-equipment"))

        mock_store_return_information.assert_called_once_with(
            email=self.leaver.email,
            requester=self.leaver,
            personal_phone="0123123123",  # /PS-IGNORE
            contact_email="joe.bloggs@example.com",  # /PS-IGNORE
            address={
                "building_and_street": "Example Building name",  # /PS-IGNORE
                "city": "Bristol",
                "county": "Bristol",
                "postcode": "AB1 2CD",  # /PS-IGNORE
            },
        )
