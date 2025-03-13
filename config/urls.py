from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path, reverse_lazy
from django.views.generic.base import RedirectView

from core.utils.urls import decorate_urlpatterns

private_urlpatterns = [
    path("", RedirectView.as_view(url=reverse_lazy("start"), permanent=False)),
    path("admin/", admin.site.urls),
    path("leavers/", include("leavers.urls")),
]
private_urlpatterns = decorate_urlpatterns(private_urlpatterns, login_required)

public_url_patterns = [
    path("", include("core.urls")),
    path("dev-tools/", include("dev_tools.urls")),
    path("auth/", include("authbroker_client.urls", namespace="authbroker")),
]

urlpatterns = private_urlpatterns + public_url_patterns
