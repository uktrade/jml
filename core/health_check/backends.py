# TODO - discuss how this can be reintroduced
# from health_check.backends import BaseHealthCheckBackend
# from health_check.exceptions import HealthCheckException

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
