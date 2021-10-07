from django.urls import path

from django_workflow_engine import workflow_urls

from leavers.views import (
    leavers_form,
    leaving_requests,
    LeaversFlowView,
    LeaversFlowListView,
    LeaversFlowCreateView,
    LeaversFlowContinueView,
)

urlpatterns = [
    path("", leaving_requests, name='leaving_requests'),
    path("new/", leavers_form, name='leavers_form'),
    path(
        "workflow/",
        workflow_urls(
            view=LeaversFlowView,
            list_view=LeaversFlowListView,
            create_view=LeaversFlowCreateView,
            continue_view=LeaversFlowContinueView,
        ),
    ),
]
