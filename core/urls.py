from typing import List, Union

from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.urls.resolvers import URLPattern, URLResolver
from django.views.decorators.cache import never_cache
from rest_framework import routers

from core.beis_service_now.api import (
    DebugApiPostView,
    ServiceNowAssetPostView,
    ServiceNowDirectoratePostView,
    ServiceNowUserPostView,
    SubmittedLeavingRequestViewSet,
)
from core.utils.urls import decorate_urlpatterns
from core.views import trigger_error
from leavers.views.api import LeavingRequestViewSet

private_urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("", include("core.landing_pages.urls")),
    path("activity-stream/", include("activity_stream.urls")),
    path("accessibility/", include("core.accessibility.urls")),
    path("cookie/", include("core.cookies.urls")),
    path("feedback/", include("core.feedback.urls")),
    path("staff-search/", include("core.staff_search.urls")),
    path("leavers/", include("leavers.urls")),
]
private_urlpatterns = decorate_urlpatterns(private_urlpatterns, login_required)


api_router = routers.DefaultRouter()

api_router.register(
    "leaving-requests",
    LeavingRequestViewSet,
    basename="leaving-requests",
)
api_router.register(
    "submitted-leaving-requests",
    SubmittedLeavingRequestViewSet,
    basename="submitted-leaving-requests",
)


public_url_patterns: List[Union[URLPattern, URLResolver]] = [
    path("", include("core.health_check.urls")),
    path("dit-activity-stream/", include("dit_activity_stream.urls")),
    path("sentry-debug/", trigger_error),
    path("api/", include((api_router.urls, "api"))),
    path(
        "api/service-now/assets/",
        ServiceNowAssetPostView.as_view(),
        name="service-now-api-assets",
    ),
    path(
        "api/service-now/users/",
        ServiceNowUserPostView.as_view(),
        name="service-now-api-users",
    ),
    path(
        "api/service-now/directorates/",
        ServiceNowDirectoratePostView.as_view(),
        name="service-now-api-directorates",
    ),
    path("api/debug-post", DebugApiPostView.as_view(), name="debug-api-post-root"),
    path("api/debug-post/", DebugApiPostView.as_view(), name="debug-api-post"),
    path(
        "api/debug-post/<path:path>",
        DebugApiPostView.as_view(),
        name="debug-api-post-path",
    ),
]

urlpatterns: List[Union[URLPattern, URLResolver]] = (
    private_urlpatterns + public_url_patterns
)
urlpatterns = decorate_urlpatterns(urlpatterns, never_cache)
