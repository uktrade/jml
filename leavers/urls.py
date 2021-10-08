from django.urls import path

from django_workflow_engine import workflow_urls

from leavers.views import (
    LeaversFlowView,
    LeaversFlowListView,
    LeaversFlowCreateView,
    LeaversFlowContinueView,
)

urlpatterns = [
    path(
        "",
        workflow_urls(
            view=LeaversFlowView,
            list_view=LeaversFlowListView,
            create_view=LeaversFlowCreateView,
            continue_view=LeaversFlowContinueView,
        ),
    ),
]
