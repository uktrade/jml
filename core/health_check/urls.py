from django.urls import path

from core.health_check.views import CustomHealthCheckView

urlpatterns = [
    path("", CustomHealthCheckView.as_view()),
]
