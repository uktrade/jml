from django.urls import path

from core.staff_search.views import StaffResultView

urlpatterns = [
    path(
        "staff-result/<uuid:staff_uuid>/",
        StaffResultView.as_view(),
        name="staff-result",
    ),
]
