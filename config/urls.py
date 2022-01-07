from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("api/", include("api.urls")),
    path("auth/", include("authbroker_client.urls", namespace="authbroker")),
    path("admin/", admin.site.urls),
    path("leavers/", include("leavers.urls")),
    path("dev-tools/", include("dev_tools.urls")),
    path("cookie/", include("core.cookies.urls")),
]
