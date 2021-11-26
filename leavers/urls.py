from django.urls import path
from django_workflow_engine import workflow_urls
from requests.api import delete

from leavers.views import leaver as leaver_views
from leavers.views.flow import (
    LeaversFlowContinueView,
    LeaversFlowCreateView,
    LeaversFlowListView,
    LeaversFlowView,
)
from leavers.views.leaving import LeaversStartView, WhoIsLeavingView
from leavers.views.line_manager import ConfirmationView, LeaverSearchView
from leavers.views.line_manager import (
    RequestReceivedView as LineManagerRequestReceivedView,
)
from leavers.views.sre import TaskConfirmationView as SRETaskConfirmationView
from leavers.views.sre import ThankYouView as SREThankYouView

urlpatterns = [
    path("", LeaversStartView.as_view(), name="start"),
    path("start/", LeaversStartView.as_view(), name="start"),
    path("who/", WhoIsLeavingView.as_view(), name="who"),
    # Line manager
    path(
        "line-manager/search/", LeaverSearchView.as_view(), name="line-manager-search"
    ),
    path(
        "line-manager/confirmation/",
        ConfirmationView.as_view(),
        name="line-manager-confirmation",
    ),
    path(
        "line-manager/request-received/",
        LineManagerRequestReceivedView.as_view(),
        name="line-manager-request-received",
    ),
    # Leaver
    path(
        "leaver/confirm-details/",
        leaver_views.ConfirmDetailsView.as_view(),
        name="leaver-confirm-details",
    ),
    path(
        "leaver/update-details/",
        leaver_views.UpdateDetailsView.as_view(),
        name="leaver-update-details",
    ),
    path("leaver/kit/", leaver_views.KitView.as_view(), name="leaver-kit"),
    path(
        "leaver/kit/delete/<uuid:kit_uuid>",
        leaver_views.delete_kit,
        name="leaver-kit-delete",
    ),
    path(
        "leaver/request-received/",
        leaver_views.RequestReceivedView.as_view(),
        name="leaver-request-received",
    ),
    # SRE
    path(
        "leaver/sre/<uuid:leaving_request_id>/",
        SRETaskConfirmationView.as_view(),
        name="sre-confirmation",
    ),
    path("leaver/sre/thank-you/", SREThankYouView.as_view(), name="sre-thank-you"),
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
