from django.urls import path

from core.health_check.views import (
    CustomHealthCheckView,
    WarningHealthCheckView,
    pingdom_healthcheck,
)

urlpatterns = [
    path("healthcheck/", CustomHealthCheckView.as_view()),
    path("healthcheck/warning", WarningHealthCheckView.as_view()),
    path("pingdom/ping.xml", pingdom_healthcheck),
]
