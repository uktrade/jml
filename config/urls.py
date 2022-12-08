from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path, reverse_lazy
from django.views.generic.base import RedirectView
from rest_framework import routers

from core.utils.urls import decorate_urlpatterns
from leavers.views.api import LeavingRequestViewSet

private_urlpatterns = [
    path("", RedirectView.as_view(url=reverse_lazy("start"), permanent=False)),
    path("admin/", admin.site.urls),
    path("assets/", include("asset_registry.urls")),
    path("leavers/", include("leavers.urls")),
]
private_urlpatterns = decorate_urlpatterns(private_urlpatterns, login_required)

router = routers.DefaultRouter()
router.register("leaving-requests", LeavingRequestViewSet, basename="leaving-requests")

public_url_patterns = [
    path("", include("core.urls")),
    path("dev-tools/", include("dev_tools.urls")),
    path("auth/", include("authbroker_client.urls", namespace="authbroker")),
    path("api/", include(router.urls)),
]

urlpatterns = private_urlpatterns + public_url_patterns
