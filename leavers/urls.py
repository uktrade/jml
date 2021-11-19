from django.urls import path

from django_workflow_engine import workflow_urls

from leavers.views.leaving import (
    LeaversStartView,
    LeavingDetailsView,
    LeavingSearchView,
    LeaverSelectionView,
    ConfirmationSummaryView,
    LeaverConfirmationView,
    LeaverConfirmedView,
)
from leavers.views.flow import (
    LeaversFlowView,
    LeaversFlowListView,
    LeaversFlowCreateView,
    LeaversFlowContinueView,
)

urlpatterns = [
    # TODO - tidy up
    path("", LeaversStartView.as_view(), name="start"),
    path("start/", LeaversStartView.as_view(), name="start"),
    path("details/", LeavingDetailsView.as_view(), name="details"),
    path("search/", LeavingSearchView.as_view(), name="search"),
    path("leaver-selection/", LeaverSelectionView.as_view(), name="leaver-selection"),
    path("confirmation/", ConfirmationSummaryView.as_view(), name="confirmation"),
    path(
        "leaver-confirmation/",
        LeaverConfirmationView.as_view(),
        name="leaver-confirmation",
    ),
    path("leaver-confirmed/", LeaverConfirmedView.as_view(), name="leaver-confirmed"),
    # path(
    #     "",
    #     workflow_urls(
    #         view=LeaversFlowView,
    #         list_view=LeaversFlowListView,
    #         create_view=LeaversFlowCreateView,
    #         continue_view=LeaversFlowContinueView,
    #     ),
    # ),
]
