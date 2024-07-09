from typing import List, Union

from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.urls.resolvers import URLPattern, URLResolver
from django.views.decorators.cache import never_cache

from core.utils.urls import decorate_urlpatterns
from core.views import trigger_error

private_urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("", include("core.landing_pages.urls")),
    path("activity-stream/", include("activity_stream.urls")),
    path("acessibility/", include("core.accessibility.urls")),
    path("cookie/", include("core.cookies.urls")),
    path("feedback/", include("core.feedback.urls")),
    path("staff-search/", include("core.staff_search.urls")),
]
private_urlpatterns = decorate_urlpatterns(private_urlpatterns, login_required)

public_url_patterns: List[Union[URLPattern, URLResolver]] = [
    path("", include("core.health_check.urls")),
    path("dit-activity-stream/", include("dit_activity_stream.urls")),
    path("sentry-debug/", trigger_error),
]

urlpatterns: List[Union[URLPattern, URLResolver]] = (
    private_urlpatterns + public_url_patterns
)
urlpatterns = decorate_urlpatterns(urlpatterns, never_cache)
