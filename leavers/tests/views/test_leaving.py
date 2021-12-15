from django.test.testcases import TestCase

from leavers.tests.views.include import ViewAccessTest


class TestLeaversStartView(ViewAccessTest, TestCase):
    view_name = "start"
    allowed_methods = ["get"]


class TestWhoIsLeavingView(ViewAccessTest, TestCase):
    view_name = "who"
    allowed_methods = ["get", "post", "put"]
