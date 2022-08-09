from django.contrib.auth.decorators import login_required
from django.urls import include, path

from core.api import PeopleFinderUpdateView
from core.utils.urls import decorate_urlpatterns

private_urlpatterns = [
    path("", include("core.landing_pages.urls")),
    path("activity-stream/", include("activity_stream.urls")),
    path("cookie/", include("core.cookies.urls")),
    path("feedback/", include("core.feedback.urls")),
]
private_urlpatterns = decorate_urlpatterns(private_urlpatterns, login_required)

public_url_patterns = [
    path("healthcheck/", include("core.health_check.urls")),
    path(
        "api/people-finder/update/",
        PeopleFinderUpdateView.as_view(),
        name="people-finder-update",
    ),
]

urlpatterns = private_urlpatterns + public_url_patterns
