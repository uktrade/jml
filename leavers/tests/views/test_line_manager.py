from datetime import date
from unittest import mock

from django.test.testcases import TestCase
from django.urls import reverse

from core.utils.staff_index import StaffDocument
from leavers.factories import LeaverInformationFactory, LeavingRequestFactory
from leavers.tests.views.include import ViewAccessTest

EMPTY_STAFF_DOCUMENT: StaffDocument = {
    "uuid": "",
    "staff_sso_activity_stream_id": "",
    "staff_sso_first_name": "",
    "staff_sso_last_name": "",
    "staff_sso_email_address": "",
    "staff_sso_contact_email_address": "",
    "people_finder_image": "",
    "people_finder_first_name": "",
    "people_finder_last_name": "",
    "people_finder_job_title": "",
    "people_finder_directorate": "",
    "people_finder_phone": "",
    "people_finder_grade": "",
    "service_now_user_id": "",
    "service_now_department_id": "",
    "service_now_department_name": "",
    "service_now_directorate_id": "",
    "service_now_directorate_name": "",
}


class TestDataRecipientSearchView(ViewAccessTest, TestCase):
    view_name = "line-manager-data-recipient-search"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        self.leaving_request = LeavingRequestFactory(
            manager_activitystream_user__email_address=self.authenticated_user.email,
        )
        self.view_kwargs = {"args": [self.leaving_request.uuid]}

    def test_search_no_results(self):
        self.client.force_login(self.authenticated_user)
        response = self.client.post(self.get_url(), {"search_terms": "bad search"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '0 results for "bad search"')

    @mock.patch(
        "core.staff_search.views.search_staff_index",
        return_value=[EMPTY_STAFF_DOCUMENT],
    )
    def test_search_with_results(self, mock_search_staff_index):
        self.client.force_login(self.authenticated_user)
        response = self.client.post(self.get_url(), {"search_terms": "example.com"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1 result for "example.com"')


class TestStartView(ViewAccessTest, TestCase):
    view_name = "line-manager-start"
    allowed_methods = ["get"]

    def setUp(self):
        super().setUp()
        self.leaving_request = LeavingRequestFactory(
            manager_activitystream_user__email_address=self.authenticated_user.email,
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


@mock.patch(
    "leavers.views.line_manager.get_staff_document_from_staff_index",
    return_value=EMPTY_STAFF_DOCUMENT,
)
class TestLeaverConfirmationView(ViewAccessTest, TestCase):
    view_name = "line-manager-leaver-confirmation"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        self.leaving_request = LeavingRequestFactory(
            manager_activitystream_user__email_address=self.authenticated_user.email,
        )
        self.view_kwargs = {"args": [self.leaving_request.uuid]}
        self.leaver_as_sso_user = self.leaving_request.leaver_activitystream_user

    def test_unauthenticated_user_get(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_unauthenticated_user_get()

    def test_unauthenticated_user_post(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_unauthenticated_user_post()

    def test_unauthenticated_user_patch(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_unauthenticated_user_patch()

    def test_unauthenticated_user_put(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_unauthenticated_user_put()

    def test_authenticated_user_get(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_authenticated_user_get()

    def test_authenticated_user_post(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_authenticated_user_post()

    def test_authenticated_user_patch(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_authenticated_user_patch()

    def test_authenticated_user_put(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_authenticated_user_put()

    """
    Functionality tests
    """

    def test_get_context(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_first_name"
        ] = self.leaver_as_sso_user.first_name
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_last_name"
        ] = self.leaver_as_sso_user.last_name

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

    def test_post_no_leaving_date(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier

        self.client.force_login(self.authenticated_user)
        response = self.client.post(self.get_url(), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_post_with_leaving_date(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier

        self.client.force_login(self.authenticated_user)
        response = self.client.post(
            self.get_url(),
            {
                "leaving_date_0": "21",
                "leaving_date_1": "12",
                "leaving_date_2": "2022",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                "line-manager-uksbs-handover",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
        )

        self.leaving_request.refresh_from_db()
        self.assertEqual(self.leaving_request.last_day.date(), date(2022, 12, 21))


@mock.patch(
    "leavers.views.line_manager.get_staff_document_from_staff_index",
    return_value=EMPTY_STAFF_DOCUMENT,
)
class TestUksbsHandoverView(ViewAccessTest, TestCase):
    view_name = "line-manager-uksbs-handover"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        self.leaving_request = LeavingRequestFactory(
            manager_activitystream_user__email_address=self.authenticated_user.email,
        )
        self.leaver_information = LeaverInformationFactory(
            leaving_request=self.leaving_request
        )
        self.view_kwargs = {"args": [self.leaving_request.uuid]}
        self.leaver_as_sso_user = self.leaving_request.leaver_activitystream_user

    def test_unauthenticated_user_get(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_unauthenticated_user_get()

    def test_unauthenticated_user_post(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_unauthenticated_user_post()

    def test_unauthenticated_user_patch(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_unauthenticated_user_patch()

    def test_unauthenticated_user_put(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_unauthenticated_user_put()

    def test_authenticated_user_get(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_authenticated_user_get()

    def test_authenticated_user_post(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_authenticated_user_post()

    def test_authenticated_user_patch(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_authenticated_user_patch()

    def test_authenticated_user_put(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        super().test_authenticated_user_put()

    """
    Functionality tests
    """

    def test_get_context(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_first_name"
        ] = self.leaver_as_sso_user.first_name
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_last_name"
        ] = self.leaver_as_sso_user.last_name

        self.leaver_information.leaver_email = self.leaver_as_sso_user.email_address
        self.leaver_information.return_personal_phone = "0123456789"
        self.leaver_information.return_address_building_and_street = "Building name"
        self.leaver_information.return_address_city = "City name"
        self.leaver_information.return_address_county = "County name"
        self.leaver_information.return_address_postcode = "PO57 C0D3"
        self.leaver_information.save()

        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["leaver_name"],
            f"{self.leaver_as_sso_user.first_name} {self.leaver_as_sso_user.last_name}",
        )
        self.assertEqual(
            response.context["leaver_email"],
            self.leaver_as_sso_user.email_address,
        )
        self.assertEqual(
            response.context["leaver_address"],
            "Building name, \nCity name, \nCounty name, \nPO57 C0D3",
        )
        self.assertEqual(
            response.context["leaver_phone"],
            "0123456789",
        )

    def test_post_no_pdf(self, mock_get_staff_document_from_staff_index):
        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier

        self.client.force_login(self.authenticated_user)
        response = self.client.post(self.get_url(), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.assertIsNone(self.leaving_request.uksbs_pdf_data)

    def test_post_with_pdf(self, mock_get_staff_document_from_staff_index):
        from django.core.files.uploadedfile import SimpleUploadedFile

        pdf_file_contents = open(
            "leavers/tests/views/data/example-empty.pdf", "rb"
        ).read()
        pdf_file = SimpleUploadedFile(
            "test.pdf", pdf_file_contents, content_type="application/pdf"
        )

        mock_get_staff_document_from_staff_index.return_value[
            "staff_sso_activity_stream_id"
        ] = self.leaver_as_sso_user.identifier

        self.client.force_login(self.authenticated_user)
        response = self.client.post(self.get_url(), {"uksbs_pdf": pdf_file})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                "line-manager-details",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
        )

        self.leaving_request.refresh_from_db()
        self.assertEqual(
            self.leaving_request.uksbs_pdf_data,
            {
                "Completed on": "",
                "Email": "",
                "Employee Number": "",
                "Last Day of Employment": "",
                "Line Manager": "",
                "Line Manager's Email": "",
                "Line Manager's Employee Number": "",
                "Line Manager's Oracle ID": "",
                "Name": "",
                "Number of Days to be Deducted": "",
                "Number of Days to be Paid": "",
                "Number of Hours to be Deducted": "",
                "Number of Hours to be Paid": "",
                "Oracle ID": "",
                "Paid or Deducted?": "",
                "Paid or Unpaid?": "",
                "Reason for Leaving": "",
                "Unit of Measurement": "",
            },
        )


class TestDetailsView(ViewAccessTest, TestCase):
    view_name = "line-manager-details"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()
        self.leaving_request = LeavingRequestFactory(
            manager_activitystream_user__email_address=self.authenticated_user.email,
        )
        self.view_kwargs = {"args": [self.leaving_request.uuid]}

    """
    Functionality tests
    """

    def test_no_data(self):
        self.client.force_login(self.authenticated_user)
        response = self.client.post(self.get_url(), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_with_data(self):
        self.client.force_login(self.authenticated_user)
        response = self.client.post(
            self.get_url(),
            {
                "security_clearance": "ctc",
                "rosa_user": "yes",
                "holds_government_procurement_card": "yes",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                "line-manager-thank-you",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
        )


class TestThankYouView(ViewAccessTest, TestCase):
    view_name = "line-manager-thank-you"
    allowed_methods = ["get"]

    def setUp(self):
        super().setUp()
        self.leaving_request = LeavingRequestFactory(
            manager_activitystream_user__email_address=self.authenticated_user.email,
        )
        self.view_kwargs = {"args": [self.leaving_request.uuid]}
