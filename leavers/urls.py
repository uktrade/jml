from django.urls import path
from django_workflow_engine import workflow_urls

from core.utils.urls import decorate_urlpatterns
from leavers.decorators import leaver_does_not_have_duplicate_person_ids
from leavers.views import admin as admin_views
from leavers.views import flow as flow_views
from leavers.views import leaver as leaver_views
from leavers.views import line_manager as line_manager_views
from leavers.views import security_team as security_team_views
from leavers.views import sre as sre_views

leaver_journey_urlpatterns = decorate_urlpatterns(
    [
        path("", leaver_views.LeaversStartView.as_view(), name="start"),
        path("start/", leaver_views.LeaversStartView.as_view(), name="start"),
        path(
            "leaver/manager-search/",
            leaver_views.MyManagerSearchView.as_view(),
            name="leaver-manager-search",
        ),
        path(
            "leaver/employment-profile/",
            leaver_views.EmploymentProfileView.as_view(),
            name="employment-profile",
        ),
        path(
            "leaver/personal-email/",
            leaver_views.LeaverFindDetailsView.as_view(),
            name="leaver-find-details",
        ),
        path(
            "leaver/personal-email-help/",
            leaver_views.LeaverFindDetailsHelpView.as_view(),
            name="leaver-find-details-help",
        ),
        path(
            "leaver/leaver-dates/remove-line-manager/",
            leaver_views.RemoveLineManagerFromLeavingRequestView.as_view(),
            name="leaver-remove-line-manager",
        ),
        path(
            "leaver/leaver-dates/",
            leaver_views.LeaverDatesView.as_view(),
            name="leaver-dates",
        ),
        path(
            "leaver/leaver-assets/",
            leaver_views.LeaverHasAssetsView.as_view(),
            name="leaver-has-assets",
        ),
        path(
            "leaver/has-cirrus-equipment/",
            leaver_views.HasCirrusEquipmentView.as_view(),
            name="leaver-has-cirrus-equipment",
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
            "leaver/contact-details/",
            leaver_views.LeaverContactDetailsView.as_view(),
            name="leaver-contact-details",
        ),
        path(
            "leaver/confirm-details/",
            leaver_views.ConfirmDetailsView.as_view(),
            name="leaver-confirm-details",
        ),
        path(
            "leaver/request-received/",
            leaver_views.RequestReceivedView.as_view(),
            name="leaver-request-received",
        ),
    ],
    leaver_does_not_have_duplicate_person_ids(),
) + [
    path(
        "leaver/person-id-error/",
        leaver_views.DuplicatePersonIdErrorView.as_view(),
        name="leaver-duplicate-person-ids-error",
    ),
]


line_manager_journey_urlpatterns = [
    path(
        "line-manager/data-recipient-search/<uuid:leaving_request_uuid>/",
        line_manager_views.DataRecipientSearchView.as_view(),
        name="line-manager-data-recipient-search",
    ),
    path(
        "line-manager/<uuid:leaving_request_uuid>/line-reports/line-manager-search/",
        line_manager_views.LineReportNewLineManagerSearchView.as_view(),
        name="line-manager-line-report-new-line-manager-search",
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
        "line-manager/<uuid:leaving_request_uuid>/leaver-confirmation/remove-data-recipient/",
        line_manager_views.RemoveDataRecipientFromLeavingRequestView.as_view(),
        name="line-manager-remove-data-recipient",
    ),
    path(
        "line-manager/<uuid:leaving_request_uuid>/details/",
        line_manager_views.DetailsView.as_view(),
        name="line-manager-details",
    ),
    path(
        "line-manager/<uuid:leaving_request_uuid>/line-reports/",
        line_manager_views.LeaverLineReportsView.as_view(),
        name="line-manager-leaver-line-reports",
    ),
    path(
        "line-manager/<uuid:leaving_request_uuid>/line-reports/remove-line-manager/",
        line_manager_views.RemoveLineManagerFromLineReportView.as_view(),
        name="remove-line-manager-from-line-report",
    ),
    path(
        "line-manager/<uuid:leaving_request_uuid>/line-reports/"
        "set-line-manager/<uuid:line_report_uuid>/",
        line_manager_views.line_report_set_new_manager,
        name="line-reports-set-new-manager",
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
    path(
        "line-manager/<uuid:leaving_request_uuid>/offline-service-now/details/",
        line_manager_views.OfflineServiceNowView.as_view(),
        name="line-manager-offline-service-now-details",
    ),
    path(
        "line-manager/<uuid:leaving_request_uuid>/offline-service-now/thank-you/",
        line_manager_views.OfflineServiceNowThankYouView.as_view(),
        name="line-manager-offline-service-now-thank-you",
    ),
]

sre_urlpatterns = [
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
        sre_views.TaskDetailView.as_view(),
        name="sre-detail",
    ),
    path(
        "leaver/sre/<uuid:leaving_request_id>/service-and-tools/<str:field_name>/",
        sre_views.TaskServiceAndToolsView.as_view(),
        name="sre-service-and-tools",
    ),
    path(
        "leaver/sre/<uuid:leaving_request_id>/confirm/",
        sre_views.TaskCompleteConfirmationView.as_view(),
        name="sre-confirm-complete",
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
]

security_urlpatterns = [
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
        "leaver/security-team/<uuid:leaving_request_id>/building-pass/",
        security_team_views.BuildingPassConfirmationView.as_view(),
        name="security-team-building-pass-confirmation",
    ),
    path(
        "leaver/security-team/<uuid:leaving_request_id>/building-pass/edit/",
        security_team_views.BuildingPassConfirmationEditView.as_view(),
        name="security-team-building-pass-confirmation-edit",
    ),
    path(
        "leaver/security-team/<uuid:leaving_request_id>/building-pass/confirm/",
        security_team_views.BuidlingPassConfirmationCloseView.as_view(),
        name="security-team-buidling-pass-confirmation-close",
    ),
    path(
        "leaver/security-team/<uuid:leaving_request_id>/rosa-kit/",
        security_team_views.RosaKitConfirmationView.as_view(),
        name="security-team-rosa-kit-confirmation",
    ),
    path(
        "leaver/security-team/<uuid:leaving_request_id>/rosa-kit/status/<str:field_name>/",
        security_team_views.RosaKitFieldView.as_view(),
        name="security-team-rosa-kit-field",
    ),
    path(
        "leaver/security-team/<uuid:leaving_request_id>/rosa-kit/confirm/",
        security_team_views.RosaKitConfirmationCloseView.as_view(),
        name="security-team-rosa-kit-confirmation-close",
    ),
    path(
        "leaver/security-team/<uuid:leaving_request_id>/summary/",
        security_team_views.TaskSummaryView.as_view(),
        name="security-team-summary",
    ),
]

admin_urlpatterns = [
    path(
        "admin/",
        admin_views.LeaversAdminView.as_view(),
        name="leavers-admin",
    ),
    path(
        "admin/leaving-requests/",
        admin_views.LeavingRequestListingView.as_view(),
        name="admin-leaving-request-listing",
    ),
    path(
        "admin/leaving-requests/<uuid:leaving_request_id>/",
        admin_views.LeavingRequestDetailView.as_view(),
        name="admin-leaving-request-detail",
    ),
    path(
        "admin/leaving-requests/<uuid:leaving_request_id>/manually-offboard-uksbs/",
        admin_views.LeavingRequestManuallyOffboarded.as_view(),
        name="admin-leaving-request-manually-offboard-uksbs",
    ),
]

workflow_urlpatterns = [
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

urlpatterns = (
    leaver_journey_urlpatterns
    + line_manager_journey_urlpatterns
    + sre_urlpatterns
    + security_urlpatterns
    + admin_urlpatterns
    + workflow_urlpatterns
)
