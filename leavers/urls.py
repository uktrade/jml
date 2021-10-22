from django.urls import path

from django_workflow_engine import workflow_urls

from leavers.views.leaving import (
    LeaversStartView,
    LeaverOrLineManagerView,
    LeavingDetailsView,
    LeavingSearchView,
    LeavingSearchResultView,
    LeavingSaveView,
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
    path("start/", LeaversStartView.as_view(), name="start"),
    path("leaver-or-line-manager/", LeaverOrLineManagerView.as_view(), name="leaver_or_line_manager"),
    path("search/", LeavingSearchView.as_view(), name="search"),
    path("search-result/", LeavingSearchResultView.as_view(), name="search-result"),
    path("saved-result/", LeavingSaveView.as_view(), name="saved"),
    path("details/", LeavingDetailsView.as_view(), name="details"),
    path("personal/", LeaverOrLineManagerView.as_view(), name="personal"),
    path("professional/", LeaverOrLineManagerView.as_view(), name="professional"),
    path("confirmation/", ConfirmationSummaryView.as_view(), name="confirmation"),
    # path(
    #     "",
    #     workflow_urls(
    #         view=LeaversFlowView,
    #         list_view=LeaversFlowListView,
    #         create_view=LeaversFlowCreateView,
    #         continue_view=LeaversFlowContinueView,
    #     ),
    # ),
    path("", LeaversStartView.as_view(), name="start"),
]
