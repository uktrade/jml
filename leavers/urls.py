from django.urls import path
from django_workflow_engine import workflow_urls

from leavers.views import flow as flow_views
from leavers.views import leaver as leaver_views
from leavers.views import leaving as leaving_views
from leavers.views import line_manager as line_manager_views
from leavers.views import report_a_leaver as report_a_leaver_views
from leavers.views import security_team as security_team_views
from leavers.views import sre as sre_views

urlpatterns = [
    path("", leaving_views.LeaversStartView.as_view(), name="start"),
    path("start/", leaving_views.LeaversStartView.as_view(), name="start"),
    path("who/", leaving_views.WhoIsLeavingView.as_view(), name="who"),
    # Report a leaver
    path(
        "report-a-leaver/leaver-search/",
        report_a_leaver_views.LeaverSearchView.as_view(),
        name="report-a-leaver-search",
    ),
    path(
        "report-a-leaver/manager-search/<uuid:leaving_request_uuid>/",
        report_a_leaver_views.ManagerSearchView.as_view(),
        name="report-a-leaver-manager-search",
    ),
    path(
        "report-a-leaver/confirmation/",
        report_a_leaver_views.ConfirmationView.as_view(),
        name="report-a-leaver-confirmation",
    ),
    path(
        "report-a-leaver/request-received/",
        report_a_leaver_views.RequestReceivedView.as_view(),
        name="report-a-leaver-request-received",
    ),
    # Leaver
    path(
        "leaver/manager-search/",
        leaver_views.MyManagerSearchView.as_view(),
        name="leaver-manager-search",
    ),
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
        leaver_views.EquipmentReturnOptionsView.as_view(),
        name="leaver-return-options",
    ),
    path(
        "leaver/return-information/",
        leaver_views.EquipmentReturnInformationView.as_view(),
        name="leaver-return-information",
    ),
    path(
        "leaver/request-received/",
        leaver_views.RequestReceivedView.as_view(),
        name="leaver-request-received",
    ),
    # Line manager return
    path(
        "line-manager/information/",
        line_manager_views.ProcessInformationView.as_view(),  # /PS-IGNORE
        name="line-manager-return-information",
    ),
    path(
        "line-manager/details/",
        line_manager_views.DetailsView.as_view(),  # /PS-IGNORE
        name="line-manager-return-details",
    ),
    path(
        "line-manager/thank-you/",
        line_manager_views.ThankYouView.as_view(),  # /PS-IGNORE
        name="line-manager-return-thank-you",
    ),
    # SRE
    path(
        "leaver/sre/<uuid:leaving_request_id>/",
        sre_views.TaskConfirmationView.as_view(),
        name="sre-confirmation",
    ),
    path(
        "leaver/sre/thank-you/<uuid:leaving_request_id>/",
        sre_views.ThankYouView.as_view(),
        name="sre-thank-you",
    ),
    # Security Team
    path(
        "leaver/security-team/<uuid:leaving_request_id>/",
        security_team_views.TaskConfirmationView.as_view(),
        name="security-team-confirmation",
    ),
    path(
        "leaver/security-team/thank-you/<uuid:leaving_request_id>/",
        security_team_views.ThankYouView.as_view(),
        name="security-team-thank-you",
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
