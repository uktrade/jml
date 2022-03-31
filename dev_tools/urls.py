from dev_tools.views import change_user, create_user, index
from django.urls import path

app_name = "dev_tools"

urlpatterns = [
    path("", index, name="index"),
    path("change-user", change_user, name="change-user"),
    path("create-user", create_user, name="create-user"),
]
