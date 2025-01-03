# TODO restore
# from unittest import mock

# from django.test import TestCase

# from core.health_check.backends import PeopleFinderHealthCheck
# from health_check.exceptions import HealthCheckException

# class TestPeopleFinderHealthCheck(TestCase):
#     def test_identifier(self):
#         people_finder_health_check = PeopleFinderHealthCheck()
#         self.assertEqual(
#             people_finder_health_check.identifier(), "People Finder Health Check"
#         )
#
#     @mock.patch(
#         "core.people_finder.interfaces.PeopleFinderStubbed.get_search_results",
#         side_effect=Exception("Error"),
#     )
#     def test_check_status_down(self, mock_get_people_finder_interface):
#         people_finder_health_check = PeopleFinderHealthCheck()
#         with self.assertRaises(HealthCheckException):
#             people_finder_health_check.check_status()
#
#     def test_check_status_up(self):
#         people_finder_health_check = PeopleFinderHealthCheck()
#         people_finder_health_check.check_status()
