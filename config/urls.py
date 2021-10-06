from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("auth/", include("authbroker_client.urls", namespace="authbroker")),
    path("admin/", admin.site.urls),
    path("", include('leavers.urls'))
]
