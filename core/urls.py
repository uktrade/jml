from django.urls import include, path

from core.api import PeopleFinderUpdateView

urlpatterns = [
    path("healthcheck/", include("core.health_check.urls")),
    path(
        "api/people-finder/update/",
        PeopleFinderUpdateView.as_view(),
        name="people-finder-update",
    ),
]
