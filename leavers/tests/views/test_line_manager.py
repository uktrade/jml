from django.test.testcases import TestCase

from leavers.tests.views.include import ViewAccessTest


class TestStartView(ViewAccessTest, TestCase):  # /PS-IGNORE
    view_name = "line-manager-start"
    allowed_methods = ["get"]


class TestDetailsView(ViewAccessTest, TestCase):  # /PS-IGNORE
    view_name = "line-manager-details"
    allowed_methods = ["get", "post", "put"]


class TestThankYouView(ViewAccessTest, TestCase):
    view_name = "line-manager-thank-you"
    allowed_methods = ["get"]
