from django.urls import path

from django_workflow_engine import workflow_urls

from leavers.views.leaving import (
    LeaversStartView,
    WhoIsLeavingView,
)
from leavers.views.line_manager import (
    LeaverSearchView,
    ConfirmationView,
    RequestReceivedView as LineManagerRequestReceivedView,
)
from leavers.views.leaver import (
    ConfirmDetailsView,
    KitView,
    UpdateDetailsView,
    RequestReceivedView as LeaverRequestReceivedView,
)

from leavers.views.flow import (
    LeaversFlowView,
    LeaversFlowListView,
    LeaversFlowCreateView,
    LeaversFlowContinueView,
)

urlpatterns = [
    path("", LeaversStartView.as_view(), name="start"),
    path("start/", LeaversStartView.as_view(), name="start"),
    path("who/", WhoIsLeavingView.as_view(), name="who"),
    # Line manager
    path("line-manager/search/", LeaverSearchView.as_view(), name="line-manager-search"),
    path("line-manager/confirmation/", ConfirmationView.as_view(), name="line-manager-confirmation"),
    path("line-manager/request-received/", LineManagerRequestReceivedView.as_view(), name="line-manager-request-received"),
    # Leaver
    path("leaver/confirm-details/", ConfirmDetailsView.as_view(), name="leaver-confirm-details"),
    path("leaver/update-details/", UpdateDetailsView.as_view(), name="leaver-update-details"),
    path("leaver/kit/", KitView.as_view(), name="leaver-kit"),
    path("leaver/request-received/", LeaverRequestReceivedView.as_view(), name="leaver-request-received"),
    # Django workflow
    path(
        "leaving-workflow/",
        workflow_urls(
            view=LeaversFlowView,
            list_view=LeaversFlowListView,
            create_view=LeaversFlowCreateView,
            continue_view=LeaversFlowContinueView,
        ),
    ),
]
