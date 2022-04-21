from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path

from core.utils.urls import decorate_urlpatterns

private_urlpatterns = decorate_urlpatterns(
    [
        path("auth/", include("authbroker_client.urls", namespace="authbroker")),
        path("admin/", admin.site.urls),
        path("assets/", include("asset_registry.urls")),
        path("leavers/", include("leavers.urls")),
        path("dev-tools/", include("dev_tools.urls")),
        path("cookie/", include("core.cookies.urls")),
    ],
    login_required,
)

public_url_patterns = [
    path("dit-activity-stream/", include("dit_activity_stream.urls")),
    path("healthcheck/", include("core.health_check.urls")),
]

urlpatterns = private_urlpatterns + public_url_patterns
