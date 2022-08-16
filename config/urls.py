from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path

from core.utils.urls import decorate_urlpatterns

private_urlpatterns = [
    path("admin/", admin.site.urls),
    path("assets/", include("asset_registry.urls")),
    path("leavers/", include("leavers.urls")),
]
private_urlpatterns = decorate_urlpatterns(private_urlpatterns, login_required)

public_url_patterns = [
    path("", include("core.urls")),
    path("dev-tools/", include("dev_tools.urls")),
    path("auth/", include("authbroker_client.urls", namespace="authbroker")),
    path("dit-activity-stream/", include("dit_activity_stream.urls")),
]

urlpatterns = private_urlpatterns + public_url_patterns

if hasattr(settings, "NESSUS_TEST_ENABLED") and settings.NESSUS_TEST_ENABLED:
    urlpatterns += [
        path("nessus/", include("nessus.urls")),
    ]
