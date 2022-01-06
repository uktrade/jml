from django.test.testcases import TestCase
from django.urls import reverse

from activity_stream.factories import ActivityStreamStaffSSOUserFactory
from leavers.tests.views.include import ViewAccessTest


class TestLeaverSearchView(ViewAccessTest, TestCase):
    view_name = "report-a-leaver-search"
    allowed_methods = ["get", "post"]


class TestConfirmationView(ViewAccessTest, TestCase):  # /PS-IGNORE
    view_name = "report-a-leaver-confirmation"
    allowed_methods = ["get", "post", "put"]
    url_query_params = "person_id=1"

    def setUp(self):
        super().setUp()  # /PS-IGNORE
        self.leaver_email = "joe.bloggs@example.com"  # /PS-IGNORE
        ActivityStreamStaffSSOUserFactory(email_address=self.leaver_email)
        session = self.client.session
        session["people_list"] = [
            {
                "staff_sso_activity_stream_id": "1",
                "email_address": self.leaver_email,
                "first_name": "Joe",  # /PS-IGNORE
                "last_name": "Bloggs",
            },
        ]
        session.save()

    def assert_authenticated_pass(self, method: str, response):
        if method not in self.allowed_methods:
            self.assertEqual(response.status_code, 405)
        elif method in ["post", "put"]:
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse("report-a-leaver-request-received"))
        else:
            self.assertEqual(response.status_code, 200)


class TestRequestReceivedView(ViewAccessTest, TestCase):
    view_name = "report-a-leaver-request-received"
    allowed_methods = ["get"]
