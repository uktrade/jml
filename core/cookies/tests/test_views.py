from django.http import SimpleCookie
from django.http.response import HttpResponse
from django.test import TestCase
from django.urls import reverse_lazy

from user.test.factories import UserFactory


class CookieNotice(TestCase):
    def test_cookie_notice(self):
        self.client.force_login(UserFactory())
        response = self.client.get(reverse_lazy("cookie-notice"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_title"], "Cookie Notice")


class CookieResponse(TestCase):
    accept_path = reverse_lazy("cookie-response", args=["accept"])
    reject_path = reverse_lazy("cookie-response", args=["reject"])

    def test_cookie_response_accept(self):
        self.client.force_login(UserFactory())
        response: HttpResponse = self.client.get(self.accept_path)

        self.assertEqual(response.status_code, 302)
        cbr_cookie: SimpleCookie = response.cookies["cookie_banner_response"]
        self.assertEqual(cbr_cookie.value, "accept")

    def test_cookie_response_reject(self):
        self.client.force_login(UserFactory())
        response: HttpResponse = self.client.get(self.reject_path)

        self.assertEqual(response.status_code, 302)
        cbr_cookie: SimpleCookie = response.cookies["cookie_banner_response"]
        self.assertEqual(cbr_cookie.value, "reject")
