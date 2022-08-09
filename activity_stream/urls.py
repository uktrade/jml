from django.urls import path

from activity_stream.views import ChoosePrimaryEmailView

urlpatterns = [
    path("", ChoosePrimaryEmailView.as_view(), name="choose_primary_email"),
]
