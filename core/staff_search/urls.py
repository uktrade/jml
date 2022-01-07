from django.urls import path

from core.staff_search import views

urlpatterns = [
    path("", views.StaffSearchView.as_view(), name="staff-search"),
]
