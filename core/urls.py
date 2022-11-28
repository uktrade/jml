from typing import List, Union

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.urls.resolvers import URLPattern, URLResolver
from django.views.decorators.cache import never_cache

from core.utils.urls import decorate_urlpatterns

private_urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("", include("core.landing_pages.urls")),
    path("activity-stream/", include("activity_stream.urls")),
    path("cookie/", include("core.cookies.urls")),
    path("feedback/", include("core.feedback.urls")),
    path("staff-search/", include("core.staff_search.urls")),
]
private_urlpatterns = decorate_urlpatterns(private_urlpatterns, login_required)

public_url_patterns: List[Union[URLPattern, URLResolver]] = [
    path("healthcheck/", include("core.health_check.urls")),
]

urlpatterns: List[Union[URLPattern, URLResolver]] = (
    private_urlpatterns + public_url_patterns
)
urlpatterns = decorate_urlpatterns(urlpatterns, never_cache)

if settings.APP_ENV == "dev":
    from django.http import HttpRequest, HttpResponse
    from django.shortcuts import render

    def error_400(request: HttpRequest) -> HttpResponse:
        return render(request, "400.html", status=400)

    def error_403(request: HttpRequest) -> HttpResponse:
        return render(request, "403.html", status=403)

    def error_404(request: HttpRequest) -> HttpResponse:
        return render(request, "404.html", status=404)

    def error_500(request: HttpRequest) -> HttpResponse:
        return render(request, "500.html", status=500)

    urlpatterns += [
        path("test-error/400/", error_400),
        path("test-error/403/", error_403),
        path("test-error/404/", error_404),
        path("test-error/500/", error_500),
    ]
