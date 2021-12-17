from django.contrib.auth.models import Group
from django.test.testcases import TestCase

from leavers.factories import LeavingRequestFactory
from leavers.tests.views.include import ViewAccessTest


class TestTaskConfirmationView(ViewAccessTest, TestCase):
    view_name = "sre-confirmation"
    allowed_methods = ["get", "post", "put"]

    def setUp(self):
        super().setUp()  # /PS-IGNORE
        sre_group, _ = Group.objects.get_or_create(name="SRE")
        self.authenticated_user.groups.add(sre_group.id)
        leaving_request = LeavingRequestFactory()
        self.view_kwargs = {"args": [leaving_request.uuid]}


class TestThankYouView(ViewAccessTest, TestCase):
    view_name = "sre-thank-you"
    allowed_methods = ["get"]

    def setUp(self):
        super().setUp()  # /PS-IGNORE
        leaving_request = LeavingRequestFactory()
        self.view_kwargs = {"args": [leaving_request.uuid]}
