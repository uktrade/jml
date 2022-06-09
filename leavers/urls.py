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
        "leaver/update-details/",
        leaver_views.UpdateDetailsView.as_view(),
        name="leaver-update-details",
    ),
    path(
        "leaver/confirm-details/",
        leaver_views.ConfirmDetailsView.as_view(),
        name="leaver-confirm-details",
    ),
    path(
        "leaver/cirrus-equipment/",
        leaver_views.CirrusEquipmentView.as_view(),
        name="leaver-cirrus-equipment",
    ),
    path(
        "leaver/cirrus-equipment/delete/<uuid:kit_uuid>",
        leaver_views.delete_cirrus_equipment,
        name="leaver-cirrus-equipment-delete",
    ),
    path(
        "leaver/cirrus-equipment/return/",
        leaver_views.CirrusEquipmentReturnOptionsView.as_view(),
        name="leaver-return-options",
    ),
    path(
        "leaver/display-screen-equipment/",
        leaver_views.DisplayScreenEquipmentView.as_view(),
        name="leaver-display-screen-equipment",
    ),
    path(
        "leaver/display-screen-equipment/delete/<uuid:kit_uuid>",
        leaver_views.delete_dse_equipment,
        name="leaver-display-screen-equipment-delete",
    ),
    path(
        "leaver/return-information/",
        leaver_views.CirrusEquipmentReturnInformationView.as_view(),
        name="leaver-return-information",
    ),
    path(
        "leaver/request-received/",
        leaver_views.RequestReceivedView.as_view(),
        name="leaver-request-received",
    ),
    # Line manager
    path(
        "line-manager/data-recipient-search/<uuid:leaving_request_uuid>/",
        line_manager_views.DataRecipientSearchView.as_view(),
        name="line-manager-data-recipient-search",
    ),
    path(
        "line-manager/<uuid:leaving_request_uuid>/information/",
        line_manager_views.StartView.as_view(),
        name="line-manager-start",
    ),
    path(
        "line-manager/<uuid:leaving_request_uuid>/leaver-confirmation/",
        line_manager_views.LeaverConfirmationView.as_view(),
        name="line-manager-leaver-confirmation",
    ),
    path(
        "line-manager/<uuid:leaving_request_uuid>/details/",
        line_manager_views.DetailsView.as_view(),
        name="line-manager-details",
    ),
    path(
        "line-manager/<uuid:leaving_request_uuid>/confirm/",
        line_manager_views.ConfirmDetailsView.as_view(),
        name="line-manager-confirmation",
    ),
    path(
        "line-manager/<uuid:leaving_request_uuid>/thank-you/",
        line_manager_views.ThankYouView.as_view(),
        name="line-manager-thank-you",
    ),
    # SRE
    path(
        "leaver/sre/complete-leaving-request/",
        sre_views.LeavingRequestListing.as_view(show_complete=True),
        name="sre-listing-complete",
    ),
    path(
        "leaver/sre/incomplete-leaving-request/",
        sre_views.LeavingRequestListing.as_view(show_incomplete=True),
        name="sre-listing-incomplete",
    ),
    path(
        "leaver/sre/<uuid:leaving_request_id>/",
        sre_views.TaskConfirmationView.as_view(),
        name="sre-confirmation",
    ),
    path(
        "leaver/sre/<uuid:leaving_request_id>/summary/",
        sre_views.TaskSummaryView.as_view(),
        name="sre-summary",
    ),
    path(
        "leaver/sre/thank-you/<uuid:leaving_request_id>/",
        sre_views.ThankYouView.as_view(),
        name="sre-thank-you",
    ),
    # Security Team
    path(
        "leaver/security-team/complete-leaving-request/",
        security_team_views.LeavingRequestListing.as_view(show_complete=True),
        name="security-team-listing-complete",
    ),
    path(
        "leaver/security-team/incomplete-leaving-request/",
        security_team_views.LeavingRequestListing.as_view(show_incomplete=True),
        name="security-team-listing-incomplete",
    ),
    path(
        "leaver/security-team/<uuid:leaving_request_id>/rosa-kit/",
        security_team_views.BuildingPassConfirmationView.as_view(),
        name="security-team-rosa-kit-confirmation",
    ),
    path(
        "leaver/security-team/<uuid:leaving_request_id>/building-pass/",
        security_team_views.BuildingPassConfirmationView.as_view(),
        name="security-team-building-pass-confirmation",
    ),
    path(
        "leaver/security-team/<uuid:leaving_request_id>/building-pass/destroy/",
        security_team_views.BuildingPassDestroyView.as_view(),
        name="security-team-building-pass-destroy",
    ),
    path(
        "leaver/security-team/<uuid:leaving_request_id>/building-pass/not-returned/",
        security_team_views.BuildingPassNotReturnedView.as_view(),
        name="security-team-building-pass-not-returned",
    ),
    path(
        "leaver/security-team/<uuid:leaving_request_id>/summary/",
        security_team_views.TaskSummaryView.as_view(),
        name="security-team-summary",
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
