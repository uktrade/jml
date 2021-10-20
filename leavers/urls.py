from django.urls import path

from django_workflow_engine import workflow_urls

from leavers.views.leaving import (
    LeaversStartView,
    LeaverOrLineManagerView,
    LeavingDetailsView,
    PersonalInfoView,
    ProfessionalInfoView,
    ConfirmationSummaryView,
)
from leavers.views.flow import (
    LeaversFlowView,
    LeaversFlowListView,
    LeaversFlowCreateView,
    LeaversFlowContinueView,
)

urlpatterns = [
    path("start/", LeaversStartView, name="start"),
    path("leaver-or-line-manager/", LeaverOrLineManagerView, name="leaver_or_line_manager"),
    path("details/", LeaverOrLineManagerView, name="details"),
    path("personal/", LeaverOrLineManagerView, name="personal"),
    path("professional/", LeaverOrLineManagerView, name="professional"),
    path("confirmation/", ConfirmationSummaryView, name="confirmation"),
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
