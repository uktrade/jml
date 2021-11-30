from django.urls import path
from django_workflow_engine import workflow_urls

from leavers.views import flow as flow_views
from leavers.views import leaver as leaver_views
from leavers.views import leaving as leaving_views
from leavers.views import line_manager as line_manager_views
from leavers.views import sre as sre_views

urlpatterns = [
    path("", leaving_views.LeaversStartView.as_view(), name="start"),
    path("start/", leaving_views.LeaversStartView.as_view(), name="start"),
    path("who/", leaving_views.WhoIsLeavingView.as_view(), name="who"),
    # Line manager
    path(
        "line-manager/search/",
        line_manager_views.LeaverSearchView.as_view(),
        name="line-manager-search",
    ),
    path(
        "line-manager/confirmation/",
        line_manager_views.ConfirmationView.as_view(),
        name="line-manager-confirmation",
    ),
    path(
        "line-manager/request-received/",
        line_manager_views.RequestReceivedView.as_view(),
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
        "leaver/return/",
        leaver_views.EquipmentReturnOption.as_view(),
        name="leaver-return-options",
    ),
    path(
        "leaver/return-information/",
        leaver_views.EquipmentReturnInformation.as_view(),
        name="leaver-return-informaation",
    ),
    path(
        "leaver/request-received/",
        leaver_views.RequestReceivedView.as_view(),
        name="leaver-request-received",
    ),
    # SRE
    path(
        "leaver/sre/<uuid:leaving_request_id>/",
        sre_views.TaskConfirmationView.as_view(),
        name="sre-confirmation",
    ),
    path(
        "leaver/sre/thank-you/",
        sre_views.ThankYouView.as_view(),
        name="sre-thank-you",
    ),
    # Django workflow
    path(
        "leaving-workflow/",
        workflow_urls(
            view=flow_views.LeaversFlowView,
            list_view=flow_views.LeaversFlowListView,
            create_view=flow_views.LeaversFlowCreateView,
            continue_view=flow_views.LeaversFlowContinueView,
        ),
    ),
]
