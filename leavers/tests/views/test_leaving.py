from django.test.testcases import TestCase
from django.urls import reverse

from leavers.tests.views.include import ViewAccessTest


class TestLeaversStartView(ViewAccessTest, TestCase):
    view_name = "start"
    allowed_methods = ["get"]


class TestWhoIsLeavingView(ViewAccessTest, TestCase):
    view_name = "who"
    allowed_methods = ["get", "post", "put"]

    def test_me(self):
        self.client.force_login(self.authenticated_user)
        response = self.client.post(self.get_url(), {"who_for": "me"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("leaver-confirm-details"))

    def test_someone_else(self):
        self.client.force_login(self.authenticated_user)
        response = self.client.post(self.get_url(), {"who_for": "someone_else"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("report-a-leaver-search"))
