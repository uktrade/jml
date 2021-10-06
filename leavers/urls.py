from django.urls import path
from leavers.views import (
    leavers_form,
    leaving_requests,
)

urlpatterns = [
    path("", leaving_requests, name='leaving_requests'),
    path("new/", leavers_form, name='leavers_form'),
]
