from unittest import mock
from uuid import uuid4

from django.contrib.auth.models import Permission
from django.test.testcases import TestCase
from django.urls import reverse
from django.utils import timezone

from activity_stream.factories import ActivityStreamStaffSSOUserFactory
from activity_stream.models import ActivityStreamStaffSSOUser
from core.utils.staff_index import StaffDocument
from leavers.factories import LeaverInformationFactory, LeavingRequestFactory
from leavers.forms.line_manager import (
    AnnualLeavePaidOrDeducted,
    DaysHours,
    FlexiLeavePaidOrDeducted,
    LeaverPaidUnpaid,
)
from leavers.tests.views.include import ViewAccessTest
from leavers.views.line_manager import LineManagerViewMixin
from user.test.factories import UserFactory

STAFF_DOCUMENT = StaffDocument.from_dict(
    {
        "uuid": uuid4(),
        "available_in_staff_sso": True,
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
EMPTY_STAFF_DOCUMENT = StaffDocument.from_dict(
    {
        "uuid": "",
        "available_in_staff_sso": True,
        "staff_sso_activity_stream_id": "",
        "staff_sso_legacy_id": "",
        "staff_sso_first_name": "",
        "staff_sso_last_name": "",
        "staff_sso_contact_email_address": "",
        "staff_sso_email_user_id": "",
        "staff_sso_email_addresses": [],
        "people_finder_first_name": "",
        "people_finder_last_name": "",
        "people_finder_job_title": "",
        "people_finder_directorate": "",
        "people_finder_phone": "",
        "people_finder_grade": "",
        "people_finder_email": "",
        "people_finder_photo": "",
        "people_finder_photo_small": "",
    }
)


class TestLineManagerAccessMixin(TestCase):
    def setUp(self):
        super().setUp()

        self.leaver = UserFactory()
        self.leaver_as_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.leaver.sso_email_user_id
        )
        self.random = UserFactory()
        self.random_as_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.random.sso_email_user_id
        )
        self.manager = UserFactory()
        self.manager_as_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.manager.sso_email_user_id
        )
        self.uksbs_manager = UserFactory()
        self.uksbs_manager_as_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.uksbs_manager.sso_email_user_id,
            uksbs_person_id=self.leaver_as_user.get_person_id() + "manager",
        )
        self.processing_manager = UserFactory()
        self.processing_manager_as_user = ActivityStreamStaffSSOUserFactory(
            email_user_id=self.processing_manager.sso_email_user_id
        )

        self.leaving_request = LeavingRequestFactory(
            leaver_complete=timezone.now(),
            leaver_activitystream_user=self.leaver_as_user,
            manager_activitystream_user=self.manager_as_user,
        )
        self.view_kwargs = {"args": [self.leaving_request.uuid]}

    def test_user_is_leaver(self):
        self.client.force_login(self.leaver)
        http_response = self.client.get("")
        response = LineManagerViewMixin().line_manager_access(
            request=http_response.wsgi_request, leaving_request=self.leaving_request
        )
        self.assertFalse(response)
        self.assertEqual(self.leaving_request.get_line_manager(), self.manager_as_user)

    def test_user_is_random(self):
        self.client.force_login(self.random)
        http_response = self.client.get("")
        response = LineManagerViewMixin().line_manager_access(
            request=http_response.wsgi_request, leaving_request=self.leaving_request
        )
        self.assertFalse(response)
        self.assertEqual(self.leaving_request.get_line_manager(), self.manager_as_user)

    def test_user_is_manager(self):
        self.client.force_login(self.manager)
        http_response = self.client.get("")
        response = LineManagerViewMixin().line_manager_access(
            request=http_response.wsgi_request, leaving_request=self.leaving_request
        )
        self.leaving_request.refresh_from_db()
        self.assertTrue(response)
        self.assertEqual(self.leaving_request.get_line_manager(), self.manager_as_user)

    def test_user_is_uksbs_manager(self):
        self.client.force_login(self.uksbs_manager)
        http_response = self.client.get("")
        response = LineManagerViewMixin().line_manager_access(
            request=http_response.wsgi_request, leaving_request=self.leaving_request
        )
        self.leaving_request.refresh_from_db()
        self.assertEqual(
            self.leaving_request.processing_manager_activitystream_user,
            self.uksbs_manager_as_user,
        )
        self.assertTrue(response)
        self.assertEqual(
            self.leaving_request.get_line_manager(), self.uksbs_manager_as_user
        )

    def test_user_has_permission(self):
        user = UserFactory()
        ActivityStreamStaffSSOUserFactory(email_user_id=user.sso_email_user_id)
        permission = Permission.objects.get(codename="select_leaver")
        user.user_permissions.add(permission)

        self.client.force_login(user)
        http_response = self.client.get("")
        response = LineManagerViewMixin().line_manager_access(
            request=http_response.wsgi_request, leaving_request=self.leaving_request
        )

        self.leaving_request.refresh_from_db()
        self.assertTrue(response)

    def test_user_is_processing_manager(self):
        self.leaving_request.processing_manager_activitystream_user = (
            self.processing_manager_as_user
        )
        self.leaving_request.save()

        self.client.force_login(self.processing_manager)
        http_response = self.client.get("")
        response = LineManagerViewMixin().line_manager_access(
            request=http_response.wsgi_request, leaving_request=self.leaving_request
        )
        self.assertFalse(response)
        self.leaving_request.refresh_from_db()
        self.assertEqual(
            self.leaving_request.processing_manager_activitystream_user,
            self.processing_manager_as_user,
        )
        self.assertEqual(self.leaving_request.get_line_manager(), self.manager_as_user)
        self.assertEqual(
            self.leaving_request.get_processing_line_manager(),
            self.processing_manager_as_user,
        )


class TestDataRecipientSearchView(ViewAccessTest, TestCase):
    view_name = "line-manager-data-recipient-search"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        email = self.authenticated_user.sso_email_user_id
        self.leaving_request = LeavingRequestFactory(
            leaver_complete=timezone.now(),
            manager_activitystream_user__email_user_id=email,
        )
        self.view_kwargs = {"args": [self.leaving_request.uuid]}

    @mock.patch(
        "core.staff_search.views.search_staff_index",
        return_value=[],
    )
    def test_search_no_results(self, mock_search_staff_index):
        self.client.force_login(self.authenticated_user)
        response = self.client.post(self.get_url(), {"search_terms": "bad search"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No results found")

    @mock.patch(
        "core.staff_search.views.search_staff_index",
        return_value=[STAFF_DOCUMENT],
    )
    def test_search_with_results(self, mock_search_staff_index):
        self.client.force_login(self.authenticated_user)
        response = self.client.post(self.get_url(), {"search_terms": "example.com"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Joe Bloggs")
        self.assertContains(
            response,
            "(Job title, joe.bloggs@example.com)",  # /PS-IGNORE
        )

        # Check that digital trade staff are excluded from the search
        exclude_staff_ids = [
            self.leaving_request.leaver_activitystream_user.identifier
        ] + [
            as_user.identifier
            for as_user in ActivityStreamStaffSSOUser.objects.without_digital_trade_email()
        ]

        mock_search_staff_index.assert_called_once_with(
            query="['example.com']",
            exclude_staff_ids=exclude_staff_ids,
        )


class TestStartView(ViewAccessTest, TestCase):
    view_name = "line-manager-start"
    allowed_methods = ["get"]

    def setUp(self):
        super().setUp()
        email = self.authenticated_user.sso_email_user_id
        self.leaving_request = LeavingRequestFactory(
            leaver_complete=timezone.now(),
            manager_activitystream_user__email_user_id=email,
        )
        self.view_kwargs = {"args": [self.leaving_request.uuid]}

    def test_get_context(self):
        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["start_url"],
            reverse(
                "line-manager-leaver-confirmation",
                kwargs={"leaving_request_uuid": str(self.leaving_request.uuid)},
            ),
        )
        self.leaving_request.refresh_from_db()
        self.assertIsNone(self.leaving_request.processing_manager_activitystream_user)


@mock.patch(
    "leavers.views.line_manager.get_staff_document_from_staff_index",
    return_value=EMPTY_STAFF_DOCUMENT,
)
class TestLeaverConfirmationView(ViewAccessTest, TestCase):
    view_name = "line-manager-leaver-confirmation"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        email = self.authenticated_user.sso_email_user_id
        self.leaving_request = LeavingRequestFactory(
            leaver_complete=timezone.now(),
            manager_activitystream_user__email_user_id=email,
        )
        self.view_kwargs = {"args": [self.leaving_request.uuid]}
        self.leaver_as_sso_user = self.leaving_request.leaver_activitystream_user

    def test_unauthenticated_user_get(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value.staff_sso_activity_stream_id = (
            self.leaver_as_sso_user.identifier
        )
        super().test_unauthenticated_user_get()

    def test_unauthenticated_user_post(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value.staff_sso_activity_stream_id = (
            self.leaver_as_sso_user.identifier
        )
        super().test_unauthenticated_user_post()

    def test_unauthenticated_user_patch(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value.staff_sso_activity_stream_id = (
            self.leaver_as_sso_user.identifier
        )
        super().test_unauthenticated_user_patch()

    def test_unauthenticated_user_put(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value.staff_sso_activity_stream_id = (
            self.leaver_as_sso_user.identifier
        )
        super().test_unauthenticated_user_put()

    def test_authenticated_user_get(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value.staff_sso_activity_stream_id = (
            self.leaver_as_sso_user.identifier
        )
        super().test_authenticated_user_get()

    def test_authenticated_user_post(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value.staff_sso_activity_stream_id = (
            self.leaver_as_sso_user.identifier
        )
        super().test_authenticated_user_post()

    def test_authenticated_user_patch(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value.staff_sso_activity_stream_id = (
            self.leaver_as_sso_user.identifier
        )
        super().test_authenticated_user_patch()

    def test_authenticated_user_put(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value.staff_sso_activity_stream_id = (
            self.leaver_as_sso_user.identifier
        )
        super().test_authenticated_user_put()

    """
    Functionality tests
    """

    def test_get_context(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value.staff_sso_activity_stream_id = (
            self.leaver_as_sso_user.identifier
        )
        mock_get_staff_document_from_staff_index.return_value.staff_sso_first_name = (
            self.leaver_as_sso_user.first_name
        )
        mock_get_staff_document_from_staff_index.return_value.staff_sso_last_name = (
            self.leaver_as_sso_user.last_name
        )

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["leaver"]["staff_sso_activity_stream_id"],
            self.leaving_request.leaver_activitystream_user.identifier,
        )
        self.assertEqual(
            response.context["leaver_name"],
            f"{self.leaver_as_sso_user.first_name} {self.leaver_as_sso_user.last_name}",
        )
        self.assertEqual(
            response.context["data_recipient"]["staff_sso_activity_stream_id"],
            self.leaving_request.leaver_activitystream_user.identifier,
        )
        self.assertEqual(
            response.context["data_recipient_search"],
            reverse(
                "line-manager-data-recipient-search",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
        )
        self.leaving_request.refresh_from_db()
        assert self.leaving_request.processing_manager_activitystream_user
        self.assertEqual(
            self.authenticated_user.sso_email_user_id,
            self.leaving_request.processing_manager_activitystream_user.email_user_id,
        )


@mock.patch(
    "leavers.views.line_manager.get_staff_document_from_staff_index",
    return_value=STAFF_DOCUMENT,
)
class TestDetailsView(ViewAccessTest, TestCase):
    view_name = "line-manager-details"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        email = self.authenticated_user.sso_email_user_id
        self.leaving_request = LeavingRequestFactory(
            leaver_complete=timezone.now(),
            manager_activitystream_user__email_user_id=email,
        )
        self.view_kwargs = {"args": [self.leaving_request.uuid]}

    """
    Functionality tests
    """

    def test_no_data(self, mocK_get_staff_document_from_staff_index):
        self.client.force_login(self.authenticated_user)
        response = self.client.post(self.get_url(), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_with_data(self, mocK_get_staff_document_from_staff_index):
        self.client.force_login(self.authenticated_user)
        response = self.client.post(
            self.get_url(),
            {
                "leaver_paid_unpaid": LeaverPaidUnpaid.PAID.value,
                "annual_leave": AnnualLeavePaidOrDeducted.PAID.value,
                "annual_leave_measurement": DaysHours.DAYS.value,
                "annual_number": "1",
                "flexi_leave": FlexiLeavePaidOrDeducted.DEDUCTED.value,
                "flexi_number": "2.5",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                "line-manager-leaver-line-reports",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
        )


class TestThankYouView(ViewAccessTest, TestCase):
    view_name = "line-manager-thank-you"
    allowed_methods = ["get"]

    def setUp(self):
        super().setUp()
        email = self.authenticated_user.sso_email_user_id
        self.leaving_request = LeavingRequestFactory(
            leaver_complete=timezone.now(),
            manager_activitystream_user__email_user_id=email,
            line_manager_complete=timezone.now(),
        )
        LeaverInformationFactory(leaving_request=self.leaving_request)
        self.view_kwargs = {"args": [self.leaving_request.uuid]}


class TestOfflineServiceNowView(ViewAccessTest, TestCase):
    view_name = "line-manager-offline-service-now-details"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        email = self.authenticated_user.sso_email_user_id
        self.leaving_request = LeavingRequestFactory(
            leaver_complete=timezone.now(),
            manager_activitystream_user__email_user_id=email,
            line_manager_complete=timezone.now(),
            service_now_offline=True,
            line_manager_service_now_complete=None,
        )
        LeaverInformationFactory(leaving_request=self.leaving_request)
        self.view_kwargs = {"args": [self.leaving_request.uuid]}

    def assert_authenticated_pass(self, method: str, response):
        if method in ["post", "put"]:
            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                response.url,
                reverse(
                    "line-manager-offline-service-now-thank-you",
                    kwargs={"leaving_request_uuid": self.leaving_request.uuid},
                ),
            )
            self.leaving_request.refresh_from_db()
            self.assertIsNotNone(self.leaving_request.line_manager_service_now_complete)
        elif method == "get":
            self.assertEqual(response.status_code, 200)


class TestOfflineServiceNowThankYouView(ViewAccessTest, TestCase):
    view_name = "line-manager-offline-service-now-thank-you"
    allowed_methods = ["get"]

    def setUp(self):
        super().setUp()
        email = self.authenticated_user.sso_email_user_id
        self.leaving_request = LeavingRequestFactory(
            leaver_complete=timezone.now(),
            manager_activitystream_user__email_user_id=email,
            line_manager_complete=timezone.now(),
            service_now_offline=True,
            line_manager_service_now_complete=timezone.now(),
        )
        LeaverInformationFactory(leaving_request=self.leaving_request)
        self.view_kwargs = {"args": [self.leaving_request.uuid]}
