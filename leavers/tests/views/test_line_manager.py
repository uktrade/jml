from django.test.testcases import TestCase

from leavers.tests.views.include import ViewAccessTest


class TestProcessInformationView(ViewAccessTest, TestCase):  # /PS-IGNORE
    view_name = "line-manager-return-information"
    allowed_methods = ["get"]


class TestDetailsView(ViewAccessTest, TestCase):  # /PS-IGNORE
    view_name = "line-manager-return-details"
    allowed_methods = ["get", "post", "put"]


class TestThankYouView(ViewAccessTest, TestCase):
    view_name = "line-manager-return-thank-you"
    allowed_methods = ["get"]
