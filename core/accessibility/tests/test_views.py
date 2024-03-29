from django.test import TestCase
from django.urls import reverse_lazy

from user.test.factories import UserFactory


class AccessibilityStatement(TestCase):
    def test_accessibility_statement(self):
        self.client.force_login(UserFactory())
        response = self.client.get(reverse_lazy("accessibility-statement"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_title"], "Accessibility statement")
