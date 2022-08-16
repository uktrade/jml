from django.contrib.auth import views as auth_views
from django.urls import path

urlpatterns = [
    path(
        "",
        auth_views.LoginView.as_view(
            template_name="nessus/test_user_login.html",
        ),
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
    ),
]
