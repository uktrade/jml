from django.conf import settings

from health_check.backends import BaseHealthCheckBackend
from health_check.exceptions import HealthCheckException


class ServiceNowHealthCheck(BaseHealthCheckBackend):
    critical_service = True

    def check_status(self):
        if not settings.SERVICE_NOW_ENABLE_ONLINE_PROCESS:
            return

        from core.service_now import get_service_now_interface

        service_now_interface = get_service_now_interface()

        try:
            service_now_interface.get_directorates()
        except Exception:
            raise HealthCheckException("Service Now is down")

    def identifier(self):
        return "Service Now Health Check"


# TODO - discuss how this can be reintroduced
# class PeopleFinderHealthCheck(BaseHealthCheckBackend):
#     critical_service = True
#
#     def check_status(self):
#         from core.people_finder import get_people_finder_interface
#
#         people_finder_search = get_people_finder_interface()
#
#         try:
#             people_finder_search.get_search_results(search_term="")
#         except Exception:
#             raise HealthCheckException("People Finder is down")
#
#     def identifier(self):
#         return "People Finder Health Check"
