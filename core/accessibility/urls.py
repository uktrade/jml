from django.urls import path

from core.accessibility import views

urlpatterns = [
    path("statement/", views.accessibility_statement, name="accessibility-statement"),
]
