from unittest import mock

from django.test import TestCase, override_settings

# from core.health_check.backends import PeopleFinderHealthCheck,
# ServiceNowHealthCheck TODO - restore
from core.health_check.backends import ServiceNowHealthCheck
from health_check.exceptions import HealthCheckException


class TestServiceNowHealthCheck(TestCase):
    def test_identifier(self):
        service_now_health_check = ServiceNowHealthCheck()
        self.assertEqual(
            service_now_health_check.identifier(), "Service Now Health Check"
        )

    @override_settings(SERVICE_NOW_ENABLE_ONLINE_PROCESS=False)
    @mock.patch(
        "core.service_now.interfaces.ServiceNowStubbed.get_directorates",
        side_effect=Exception("Error"),
    )
    def test_check_status_down_when_disabled(self, mock_get_service_now_interface):
        service_now_health_check = ServiceNowHealthCheck()
        service_now_health_check.check_status()

    @override_settings(SERVICE_NOW_ENABLE_ONLINE_PROCESS=True)
    @mock.patch(
        "core.service_now.interfaces.ServiceNowStubbed.get_directorates",
        side_effect=Exception("Error"),
    )
    def test_check_status_down_when_enabled(self, mock_get_service_now_interface):
        service_now_health_check = ServiceNowHealthCheck()
        with self.assertRaises(HealthCheckException):
            service_now_health_check.check_status()

    def test_check_status_up(self):
        service_now_health_check = ServiceNowHealthCheck()
        service_now_health_check.check_status()


# TODO restore
# class TestPeopleFinderHealthCheck(TestCase):
#     def test_identifier(self):
#         service_now_health_check = PeopleFinderHealthCheck()
#         self.assertEqual(
#             service_now_health_check.identifier(), "People Finder Health Check"
#         )
#
#     @mock.patch(
#         "core.people_finder.interfaces.PeopleFinderStubbed.get_search_results",
#         side_effect=Exception("Error"),
#     )
#     def test_check_status_down(self, mock_get_service_now_interface):
#         service_now_health_check = PeopleFinderHealthCheck()
#         with self.assertRaises(HealthCheckException):
#             service_now_health_check.check_status()
#
#     def test_check_status_up(self):
#         service_now_health_check = PeopleFinderHealthCheck()
#         service_now_health_check.check_status()
