from django.urls import path

from core.health_check.views import CustomHealthCheckView, WarningHealthCheckView

urlpatterns = [
    path("", CustomHealthCheckView.as_view()),
    path("warning", WarningHealthCheckView.as_view()),
]
