from django.urls import include, path

from core.api import people_finder_update

urlpatterns = [
    path("healthcheck/", include("core.health_check.urls")),
    path(
        "api/people-finder/update/", people_finder_update, name="people-finder-update"
    ),
]
