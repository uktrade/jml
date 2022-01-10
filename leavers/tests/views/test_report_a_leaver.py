from unittest import mock

from django.test.testcases import TestCase
from django.urls import reverse

from activity_stream.factories import ActivityStreamStaffSSOUserFactory
from core.utils.staff_index import StaffDocument
from leavers.tests.views.include import ViewAccessTest

EMPTY_STAFF_DOCUMENT: StaffDocument = {
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


@mock.patch(
    "leavers.views.report_a_leaver.get_staff_document_from_staff_index",
    return_value=EMPTY_STAFF_DOCUMENT,
)
# @mock.patch(
#     "core.utils.staff_index.get_staff_document_from_staff_index",
#     return_value=EMPTY_STAFF_DOCUMENT,
# )
class TestConfirmationView(ViewAccessTest, TestCase):  # /PS-IGNORE
    view_name = "report-a-leaver-confirmation"
    allowed_methods = ["get", "post", "put"]
    url_query_params = "person_id=1"

    def setUp(self):
        super().setUp()  # /PS-IGNORE
        self.leaver_email = "joe.bloggs@example.com"  # /PS-IGNORE
        self.leaver_as_sso_user = ActivityStreamStaffSSOUserFactory(
            email_address=self.leaver_email
        )
        self.manager_as_sso_user = ActivityStreamStaffSSOUserFactory()
        session = self.client.session
        session["leaver_id"] = self.leaver_as_sso_user.identifier
        session["manager_id"] = self.manager_as_sso_user.identifier
        session.save()

    def assert_authenticated_pass(self, method: str, response):
        if method not in self.allowed_methods:
            self.assertEqual(response.status_code, 405)
        elif method in ["post", "put"]:
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse("report-a-leaver-request-received"))
        else:
            self.assertEqual(response.status_code, 200)

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


class TestRequestReceivedView(ViewAccessTest, TestCase):
    view_name = "report-a-leaver-request-received"
    allowed_methods = ["get"]
