from django.urls import path

from core.cookies import views

urlpatterns = [
    path("notice/", views.cookie_notice, name="cookie-notice"),
    path(
        "response/<str:response>/",
        views.cookie_response,
        name="cookie-response",
    ),
]
