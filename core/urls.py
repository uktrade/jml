from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.decorators.cache import never_cache

from core.utils.urls import decorate_urlpatterns

private_urlpatterns = [
    path("", include("core.landing_pages.urls")),
    path("activity-stream/", include("activity_stream.urls")),
    path("cookie/", include("core.cookies.urls")),
    path("feedback/", include("core.feedback.urls")),
    path("staff-search/", include("core.staff_search.urls")),
]
private_urlpatterns = decorate_urlpatterns(private_urlpatterns, login_required)

public_url_patterns = [
    path("healthcheck/", include("core.health_check.urls")),
]

urlpatterns = private_urlpatterns + public_url_patterns
urlpatterns = decorate_urlpatterns(urlpatterns, never_cache)
