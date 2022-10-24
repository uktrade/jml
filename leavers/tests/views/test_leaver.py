from datetime import date, datetime
from unittest import mock
from uuid import uuid4

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from activity_stream.factories import ActivityStreamStaffSSOUserFactory
from core.utils.staff_index import StaffDocument
from leavers.factories import LeaverInformationFactory, LeavingRequestFactory
from leavers.models import LeavingRequest
from leavers.types import ReturnOptions, SecurityClearance, StaffType
from leavers.views.leaver import LINE_MANAGER_SEARCH_PARAM
from user.test.factories import UserFactory

STAFF_DOCUMENT = StaffDocument.from_dict(
    {
        "uuid": uuid4(),
        "staff_sso_activity_stream_id": "1",
        "staff_sso_legacy_id": "123",
        "staff_sso_contact_email_address": "joe.bloggs@example.com",  # /PS-IGNORE
        "staff_sso_first_name": "Joe",  # /PS-IGNORE
        "staff_sso_last_name": "Bloggs",
        "staff_sso_email_user_id": "joe.bloggs@example.com",  # /PS-IGNORE
        "staff_sso_email_addresses": [
            "joe.bloggs@example.com",  # /PS-IGNORE
        ],
        "people_finder_directorate": "",
        "people_finder_first_name": "Joe",  # /PS-IGNORE
        "people_finder_grade": "Example Grade",
        "people_finder_job_title": "Job title",
        "people_finder_last_name": "Bloggs",
        "people_finder_phone": "0123456789",
        "people_finder_email": "joe.bloggs@example.com",  # /PS-IGNORE
        "people_finder_photo": "",
        "people_finder_photo_small": "",
    }
)


class TestMyManagerSearchView(TestCase):
    view_name = "leaver-manager-search"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.leaver.sso_email_user_id,
        )

    def test_unauthenticated_user(self) -> None:
        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 302)
        self.assertTrue(get_response["Location"].startswith(reverse("dev_tools:index")))

        post_response = self.client.post(reverse(self.view_name), data={})

        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(
            post_response["Location"].startswith(reverse("dev_tools:index"))
        )

    @mock.patch(
        "core.staff_search.views.search_staff_index",
        return_value=[],
    )
    def test_authenticated_user_no_results(self, mock_search_staff_index):
        self.client.force_login(self.leaver)

        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, "No results found")

        post_response = self.client.post(reverse(self.view_name), data={})

        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, "No results found")

    @mock.patch(
        "core.staff_search.views.search_staff_index",
        return_value=[STAFF_DOCUMENT],
    )
    def test_authenticated_user_with_results(self, mock_search_staff_index):
        self.client.force_login(self.leaver)

        post_response = self.client.post(
            reverse(self.view_name),
            data={
                "search_terms": "joe",
            },
        )

        self.assertEqual(post_response.status_code, 200)
        self.assertNotContains(post_response, "No results found")
        self.assertContains(post_response, "Joe Bloggs")  # /PS-IGNORE
        self.assertContains(
            post_response,
            "Job title, joe.bloggs@example.com",  # /PS-IGNORE
        )
        self.assertContains(
            post_response,
            f"?{LINE_MANAGER_SEARCH_PARAM}={STAFF_DOCUMENT.uuid}",
        )


class TestEmploymentProfileView(TestCase):
    view_name = "employment-profile"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.leaver.sso_email_user_id,
        )

    def test_unauthenticated_user(self) -> None:
        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 302)
        self.assertTrue(get_response["Location"].startswith(reverse("dev_tools:index")))

        post_response = self.client.post(reverse(self.view_name), data={})

        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(
            post_response["Location"].startswith(reverse("dev_tools:index"))
        )

    def test_authenticated_user(self):
        self.client.force_login(self.leaver)

        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, "Your employment profile")

        post_response = self.client.post(reverse(self.view_name), data={})

        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, "There is a problem")

        # Ensure we skip the view if the leaver process is already completed.
        leaving_request = LeavingRequest.objects.get(
            leaver_activitystream_user=self.leaver_activity_stream_user
        )
        leaving_request.leaver_complete = timezone.now()
        leaving_request.save()
        already_completed_response = self.client.get(reverse(self.view_name))

        self.assertEqual(already_completed_response.status_code, 302)
        self.assertEqual(
            already_completed_response["Location"], reverse("leaver-request-received")
        )

    def test_post_form_data(self):
        self.client.force_login(self.leaver)

        post_response = self.client.post(
            reverse(self.view_name),
            data={
                "first_name": "Charlie",
                "last_name": "Croker",
                "date_of_birth_0": "6",
                "date_of_birth_1": "2",
                "date_of_birth_2": "2000",
                "job_title": "Developer",
                "staff_type": StaffType.CIVIL_SERVANT.value,
                "security_clearance": SecurityClearance.SC.value,
            },
        )

        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(post_response["Location"], reverse("leaver-find-details"))

        leaving_request = LeavingRequest.objects.get(
            leaver_activitystream_user=self.leaver_activity_stream_user
        )
        self.assertEqual(leaving_request.staff_type, StaffType.CIVIL_SERVANT.value)
        self.assertEqual(leaving_request.security_clearance, SecurityClearance.SC.value)

        leaver_info = leaving_request.leaver_information.first()
        self.assertEqual(leaver_info.leaver_first_name, "Charlie")
        self.assertEqual(leaver_info.leaver_last_name, "Croker")
        self.assertEqual(leaver_info.leaver_date_of_birth, date(2000, 2, 6))
        self.assertEqual(leaver_info.job_title, "Developer")


class TestRemoveLineManagerFromLeavingRequestView(TestCase):
    view_name = "leaver-remove-line-manager"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.leaver.sso_email_user_id,
        )
        self.leaving_request = LeavingRequestFactory(
            leaver_activitystream_user=self.leaver_activity_stream_user,
        )

    def test_unauthenticated_user(self) -> None:
        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 302)
        self.assertTrue(get_response["Location"].startswith(reverse("dev_tools:index")))

        post_response = self.client.post(reverse(self.view_name), data={})

        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(
            post_response["Location"].startswith(reverse("dev_tools:index"))
        )

    def test_authenticated_user(self):
        self.client.force_login(self.leaver)

        self.leaving_request.manager_activitystream_user = (
            ActivityStreamStaffSSOUserFactory()
        )
        self.leaving_request.save()

        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 302)
        self.assertEqual(get_response["Location"], reverse("leaver-dates"))
        self.leaving_request.refresh_from_db()
        self.assertIsNone(self.leaving_request.manager_activitystream_user)

        # Ensure we skip the view if the leaver process is already completed.
        self.leaving_request.leaver_complete = timezone.now()
        self.leaving_request.save()
        already_completed_response = self.client.get(reverse(self.view_name))

        self.assertEqual(already_completed_response.status_code, 302)
        self.assertEqual(
            already_completed_response["Location"], reverse("leaver-request-received")
        )


class TestLeaverDatesView(TestCase):
    view_name = "leaver-dates"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.leaver.sso_email_user_id,
        )
        self.leaving_request = LeavingRequestFactory(
            leaver_activitystream_user=self.leaver_activity_stream_user,
            manager_activitystream_user=ActivityStreamStaffSSOUserFactory(),
        )

    def test_unauthenticated_user(self) -> None:
        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 302)
        self.assertTrue(get_response["Location"].startswith(reverse("dev_tools:index")))

        post_response = self.client.post(reverse(self.view_name), data={})

        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(
            post_response["Location"].startswith(reverse("dev_tools:index"))
        )

    @mock.patch(
        "core.utils.staff_index.get_staff_document_from_staff_index",
        return_value=STAFF_DOCUMENT,
    )
    def test_authenticated_user(self, mock_get_staff_document_from_staff_index):
        self.client.force_login(self.leaver)

        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 200)

        # Ensure we skip the view if the leaver process is already completed.
        self.leaving_request.leaver_complete = timezone.now()
        self.leaving_request.save()
        already_completed_response = self.client.get(reverse(self.view_name))

        self.assertEqual(already_completed_response.status_code, 302)
        self.assertEqual(
            already_completed_response["Location"], reverse("leaver-request-received")
        )

    @mock.patch(
        "core.utils.staff_index.get_staff_document_from_staff_index",
        return_value=STAFF_DOCUMENT,
    )
    def test_post_form_data(self, mock_get_staff_document_from_staff_index):
        self.client.force_login(self.leaver)

        post_response = self.client.post(
            reverse(self.view_name),
            data={
                "leaving_date_0": "1",
                "leaving_date_1": "2",
                "leaving_date_2": "2023",
                "last_day_0": "1",
                "last_day_1": "2",
                "last_day_2": "2023",
                "leaver_manager": STAFF_DOCUMENT.uuid,
            },
        )

        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(post_response["Location"], reverse("leaver-has-assets"))

        leaver_info = self.leaving_request.leaver_information.first()
        self.assertEqual(
            leaver_info.leaving_date, timezone.make_aware(datetime(2023, 2, 1))
        )
        self.assertEqual(
            leaver_info.last_day, timezone.make_aware(datetime(2023, 2, 1))
        )

    @mock.patch(
        "core.utils.staff_index.get_staff_document_from_staff_index",
        return_value=STAFF_DOCUMENT,
    )
    def test_post_form_data_no_manager(self, mock_get_staff_document_from_staff_index):
        self.client.force_login(self.leaver)

        self.leaving_request.manager_activitystream_user = None
        self.leaving_request.save()

        post_response = self.client.post(
            reverse(self.view_name),
            data={
                "leaving_date_0": "1",
                "leaving_date_1": "2",
                "leaving_date_2": "2023",
                "last_day_0": "1",
                "last_day_1": "2",
                "last_day_2": "2023",
                "leaver_manager": STAFF_DOCUMENT.uuid,
            },
        )

        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, "You must select a line manager")


class TestLeaverHasAssetsView(TestCase):
    view_name = "leaver-has-assets"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.leaver.sso_email_user_id,
        )
        self.leaving_request = LeavingRequestFactory(
            leaver_activitystream_user=self.leaver_activity_stream_user,
            manager_activitystream_user=ActivityStreamStaffSSOUserFactory(),
        )

    def test_unauthenticated_user(self) -> None:
        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 302)
        self.assertTrue(get_response["Location"].startswith(reverse("dev_tools:index")))

        post_response = self.client.post(reverse(self.view_name), data={})

        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(
            post_response["Location"].startswith(reverse("dev_tools:index"))
        )

    def test_authenticated_user(self):
        self.client.force_login(self.leaver)

        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 200)

        # Ensure we skip the view if the leaver process is already completed.
        self.leaving_request.leaver_complete = timezone.now()
        self.leaving_request.save()
        already_completed_response = self.client.get(reverse(self.view_name))

        self.assertEqual(already_completed_response.status_code, 302)
        self.assertEqual(
            already_completed_response["Location"], reverse("leaver-request-received")
        )

    def test_post_form_data(self):
        self.client.force_login(self.leaver)

        post_response = self.client.post(
            reverse(self.view_name),
            data={
                "has_gov_procurement_card": "yes",
                "has_rosa_kit": "yes",
                "has_dse": "yes",
            },
        )

        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(
            post_response["Location"], reverse("leaver-has-cirrus-equipment")
        )

        self.leaving_request.refresh_from_db()
        self.assertTrue(self.leaving_request.holds_government_procurement_card)
        self.assertTrue(self.leaving_request.is_rosa_user)

        leaver_info = self.leaving_request.leaver_information.first()
        self.assertTrue(leaver_info.has_dse)


class TestHasCirrusEquipmentView(TestCase):
    view_name = "leaver-has-cirrus-equipment"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.leaver.sso_email_user_id,
        )
        self.leaving_request = LeavingRequestFactory(
            leaver_activitystream_user=self.leaver_activity_stream_user,
            manager_activitystream_user=ActivityStreamStaffSSOUserFactory(),
        )

    def test_unauthenticated_user(self) -> None:
        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 302)
        self.assertTrue(get_response["Location"].startswith(reverse("dev_tools:index")))

        post_response = self.client.post(reverse(self.view_name), data={})

        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(
            post_response["Location"].startswith(reverse("dev_tools:index"))
        )

    @mock.patch(
        "leavers.views.leaver.get_cirrus_assets",
        return_value=[
            {
                "uuid": "00000000-0000-0000-0000-000000000000",
                "sys_id": 1,
                "name": "Test Asset",
                "tag": "TAG123",
            }
        ],
    )
    def test_authenticated_user(self, mock_get_cirrus_assets):
        self.client.force_login(self.leaver)

        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 302)
        self.assertEqual(get_response["Location"], reverse("leaver-cirrus-equipment"))

        mock_get_cirrus_assets.return_value = []

        get_response_no_assets = self.client.get(reverse(self.view_name))
        self.assertEqual(get_response_no_assets.status_code, 200)

        # Ensure we skip the view if the leaver process is already completed.
        self.leaving_request.leaver_complete = timezone.now()
        self.leaving_request.save()
        already_completed_response = self.client.get(reverse(self.view_name))

        self.assertEqual(already_completed_response.status_code, 302)
        self.assertEqual(
            already_completed_response["Location"], reverse("leaver-request-received")
        )

    @mock.patch(
        "leavers.views.leaver.get_cirrus_assets",
        return_value=[],
    )
    def test_post_form_data(self, mock_get_cirrus_assets):
        self.client.force_login(self.leaver)

        post_response = self.client.post(
            reverse(self.view_name),
            data={
                "has_cirrus_kit": "yes",
            },
        )

        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(post_response["Location"], reverse("leaver-cirrus-equipment"))

        post_response = self.client.post(
            reverse(self.view_name),
            data={
                "has_cirrus_kit": "no",
            },
        )

        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(
            post_response["Location"], reverse("leaver-display-screen-equipment")
        )


class TestCirrusEquipmentView(TestCase):
    view_name = "leaver-cirrus-equipment"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.leaver.sso_email_user_id,
        )
        self.leaving_request = LeavingRequestFactory(
            leaver_activitystream_user=self.leaver_activity_stream_user,
            manager_activitystream_user=ActivityStreamStaffSSOUserFactory(),
        )

    def test_unauthenticated_user(self) -> None:
        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 302)
        self.assertTrue(get_response["Location"].startswith(reverse("dev_tools:index")))

        post_response = self.client.post(reverse(self.view_name), data={})

        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(
            post_response["Location"].startswith(reverse("dev_tools:index"))
        )

    def test_authenticated_user(self):
        self.client.force_login(self.leaver)

        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 200)

        # Ensure we skip the view if the leaver process is already completed.
        self.leaving_request.leaver_complete = timezone.now()
        self.leaving_request.save()
        already_completed_response = self.client.get(reverse(self.view_name))

        self.assertEqual(already_completed_response.status_code, 302)
        self.assertEqual(
            already_completed_response["Location"], reverse("leaver-request-received")
        )

    def test_post_add_asset_form(self):
        self.client.force_login(self.leaver)

        post_response = self.client.post(
            reverse(self.view_name),
            data={
                "form_name": "add_asset_form",
                "asset_name": "New test asset",
            },
        )

        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(post_response["Location"], reverse("leaver-cirrus-equipment"))

        cirrus_assets = post_response.wsgi_request.session["cirrus_assets"]
        self.assertEqual(len(cirrus_assets), 1)
        self.assertEqual(cirrus_assets[0]["name"], "New test asset")

    def test_post_cirrus_return_office_form(self):
        self.client.force_login(self.leaver)

        post_response = self.client.post(
            reverse(self.view_name),
            data={
                "form_name": "cirrus_return_form",
                "return_option": ReturnOptions.OFFICE.value,
                "office_personal_phone": "0123123123",
                "office_contact_email": "someone@example.com",  # /PS-IGNORE
                "home_personal_phone": "",
                "home_contact_email": "",
                "home_address_line_1": "",
                "home_address_line_2": "",
                "home_address_city": "",
                "home_address_county": "",
                "home_address_postcode": "",
            },
        )

        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(
            post_response["Location"], reverse("leaver-display-screen-equipment")
        )

        leaver_info = self.leaving_request.leaver_information.first()
        self.assertEqual(leaver_info.return_personal_phone, "0123123123")
        self.assertEqual(
            leaver_info.return_contact_email,
            "someone@example.com",  # /PS-IGNORE
        )
        self.assertEqual(leaver_info.return_address_line_1, None)
        self.assertEqual(leaver_info.return_address_line_2, None)
        self.assertEqual(leaver_info.return_address_city, None)
        self.assertEqual(leaver_info.return_address_county, None)
        self.assertEqual(leaver_info.return_address_postcode, None)

    def test_post_cirrus_return_home_form(self):
        self.client.force_login(self.leaver)

        post_response = self.client.post(
            reverse(self.view_name),
            data={
                "form_name": "cirrus_return_form",
                "return_option": ReturnOptions.HOME.value,
                "office_personal_phone": "",
                "office_contact_email": "",
                "home_personal_phone": "0123123123",
                "home_contact_email": "someone@example.com",  # /PS-IGNORE
                "home_address_line_1": "Line 1",
                "home_address_line_2": "Line 2",
                "home_address_city": "City",
                "home_address_county": "County",
                "home_address_postcode": "Postcode",
            },
        )

        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(
            post_response["Location"], reverse("leaver-display-screen-equipment")
        )

        leaver_info = self.leaving_request.leaver_information.first()
        self.assertEqual(leaver_info.return_personal_phone, "0123123123")
        self.assertEqual(
            leaver_info.return_contact_email,
            "someone@example.com",  # /PS-IGNORE
        )
        self.assertEqual(leaver_info.return_address_line_1, "Line 1")
        self.assertEqual(leaver_info.return_address_line_2, "Line 2")
        self.assertEqual(leaver_info.return_address_city, "City")
        self.assertEqual(leaver_info.return_address_county, "County")
        self.assertEqual(leaver_info.return_address_postcode, "Postcode")

    def test_post_cirrus_return_form_no_assets(self):
        self.client.force_login(self.leaver)

        post_response = self.client.post(
            reverse(self.view_name),
            data={
                "form_name": "cirrus_return_form_no_assets",
            },
        )

        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(
            post_response["Location"], reverse("leaver-display-screen-equipment")
        )

        leaver_info = self.leaving_request.leaver_information.first()
        self.assertEqual(leaver_info.cirrus_assets, [])


class TestDisplayScreenEquipmentView(TestCase):
    view_name = "leaver-display-screen-equipment"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.leaver.sso_email_user_id,
        )
        self.leaving_request = LeavingRequestFactory(
            leaver_activitystream_user=self.leaver_activity_stream_user,
            manager_activitystream_user=ActivityStreamStaffSSOUserFactory(),
        )
        self.leaver_info = LeaverInformationFactory(
            leaving_request=self.leaving_request,
            has_dse=True,
        )

    def test_unauthenticated_user(self) -> None:
        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 302)
        self.assertTrue(get_response["Location"].startswith(reverse("dev_tools:index")))

        post_response = self.client.post(reverse(self.view_name), data={})

        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(
            post_response["Location"].startswith(reverse("dev_tools:index"))
        )

    def test_authenticated_user(self):
        self.client.force_login(self.leaver)

        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 200)

        # Ensure we skip the view if the leaver process is already completed.
        self.leaving_request.leaver_complete = timezone.now()
        self.leaving_request.save()
        already_completed_response = self.client.get(reverse(self.view_name))

        self.assertEqual(already_completed_response.status_code, 302)
        self.assertEqual(
            already_completed_response["Location"], reverse("leaver-request-received")
        )

    def test_post_add_asset_form(self):
        self.client.force_login(self.leaver)

        post_response = self.client.post(
            reverse(self.view_name),
            data={
                "form_name": "add_asset_form",
                "asset_name": "New test asset",
            },
        )

        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(
            post_response["Location"], reverse("leaver-display-screen-equipment")
        )

        dse_assets = post_response.wsgi_request.session["dse_assets"]
        self.assertEqual(len(dse_assets), 1)
        self.assertEqual(dse_assets[0]["name"], "New test asset")

    def test_post_submission_form(self):
        self.client.force_login(self.leaver)

        post_response = self.client.post(
            reverse(self.view_name),
            data={
                "form_name": "submission_form",
            },
        )

        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(post_response["Location"], reverse("leaver-contact-details"))

        leaver_info = self.leaving_request.leaver_information.first()
        self.assertEqual(leaver_info.dse_assets, [])


class TestLeaverContactDetailsView(TestCase):
    view_name = "leaver-contact-details"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.leaver.sso_email_user_id,
        )
        self.leaving_request = LeavingRequestFactory(
            leaver_activitystream_user=self.leaver_activity_stream_user,
            manager_activitystream_user=ActivityStreamStaffSSOUserFactory(),
        )
        self.leaver_info = LeaverInformationFactory(
            leaving_request=self.leaving_request,
            has_dse=True,
        )

    def test_unauthenticated_user(self) -> None:
        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 302)
        self.assertTrue(get_response["Location"].startswith(reverse("dev_tools:index")))

        post_response = self.client.post(reverse(self.view_name), data={})

        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(
            post_response["Location"].startswith(reverse("dev_tools:index"))
        )

    def test_authenticated_user(self):
        self.client.force_login(self.leaver)

        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 200)

        # Ensure we skip the view if the leaver process is already completed.
        self.leaving_request.leaver_complete = timezone.now()
        self.leaving_request.save()
        already_completed_response = self.client.get(reverse(self.view_name))

        self.assertEqual(already_completed_response.status_code, 302)
        self.assertEqual(
            already_completed_response["Location"], reverse("leaver-request-received")
        )

    def test_post_form(self):
        self.client.force_login(self.leaver)

        post_response = self.client.post(
            reverse(self.view_name),
            data={
                "contact_phone": "0123123123",
                "contact_email_address": "contact@email.com",  # /PS-IGNORE
                "contact_address_line_1": "Line 1",
                "contact_address_line_2": "Line 2",
                "contact_address_city": "City",
                "contact_address_county": "County",
                "contact_address_postcode": "Postcode",
            },
        )

        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(post_response["Location"], reverse("leaver-confirm-details"))

        self.leaver_info.refresh_from_db()
        self.assertEqual(self.leaver_info.contact_phone, "0123123123")
        self.assertEqual(
            self.leaver_info.personal_email,
            "contact@email.com",  # /PS-IGNORE
        )
        self.assertEqual(self.leaver_info.contact_address_line_1, "Line 1")
        self.assertEqual(self.leaver_info.contact_address_line_2, "Line 2")
        self.assertEqual(self.leaver_info.contact_address_city, "City")
        self.assertEqual(self.leaver_info.contact_address_county, "County")
        self.assertEqual(self.leaver_info.contact_address_postcode, "Postcode")


class TestConfirmDetailsView(TestCase):
    view_name = "leaver-confirm-details"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.leaver.sso_email_user_id,
        )
        self.leaving_request = LeavingRequestFactory(
            leaver_activitystream_user=self.leaver_activity_stream_user,
            manager_activitystream_user=ActivityStreamStaffSSOUserFactory(),
            staff_type=StaffType.CIVIL_SERVANT.value,
            security_clearance=SecurityClearance.SC.value,
        )
        self.leaver_info = LeaverInformationFactory(
            leaving_request=self.leaving_request,
            has_dse=True,
        )

    def test_unauthenticated_user(self) -> None:
        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 302)
        self.assertTrue(get_response["Location"].startswith(reverse("dev_tools:index")))

        post_response = self.client.post(reverse(self.view_name), data={})

        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(
            post_response["Location"].startswith(reverse("dev_tools:index"))
        )

    def test_authenticated_user(self):
        self.client.force_login(self.leaver)

        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 200)

        # Ensure we skip the view if the leaver process is already completed.
        self.leaving_request.leaver_complete = timezone.now()
        self.leaving_request.save()
        already_completed_response = self.client.get(reverse(self.view_name))

        self.assertEqual(already_completed_response.status_code, 302)
        self.assertEqual(
            already_completed_response["Location"], reverse("leaver-request-received")
        )

    def test_post_form(self):
        self.client.force_login(self.leaver)

        post_response = self.client.post(
            reverse(self.view_name),
            data={},
        )

        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(post_response["Location"], reverse("leaver-request-received"))


class TestRequestReceivedView(TestCase):
    view_name = "leaver-request-received"

    def setUp(self) -> None:
        self.leaver = UserFactory()
        self.leaver_activity_stream_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.leaver.sso_email_user_id,
        )
        self.leaving_request = LeavingRequestFactory(
            leaver_activitystream_user=self.leaver_activity_stream_user,
            manager_activitystream_user=ActivityStreamStaffSSOUserFactory(),
        )
        self.leaver_info = LeaverInformationFactory(
            leaving_request=self.leaving_request,
            has_dse=True,
        )

    def test_unauthenticated_user(self) -> None:
        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 302)
        self.assertTrue(get_response["Location"].startswith(reverse("dev_tools:index")))

        post_response = self.client.post(reverse(self.view_name), data={})

        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(
            post_response["Location"].startswith(reverse("dev_tools:index"))
        )

    def test_authenticated_user(self):
        self.client.force_login(self.leaver)

        get_response = self.client.get(reverse(self.view_name))

        self.assertEqual(get_response.status_code, 200)

        # Ensure we skip the view if the leaver process is already completed.
        self.leaving_request.leaver_complete = timezone.now()
        self.leaving_request.save()
        already_completed_response = self.client.get(reverse(self.view_name))

        self.assertEqual(already_completed_response.status_code, 200)
