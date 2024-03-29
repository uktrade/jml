from typing import Dict

from django.urls import URLPattern, URLResolver, include, path, reverse_lazy
from django.views.generic.base import RedirectView
from django_workflow_engine import workflow_urls

from leavers.views import admin as admin_views
from leavers.views import common as common_views
from leavers.views import flow as flow_views
from leavers.views import leaver as leaver_views
from leavers.views import line_manager as line_manager_views
from leavers.views import security_team as security_team_views
from leavers.views import sre as sre_views

leaving_request_review_urlpatterns = [
    path(
        "data-recipient-search/",
        line_manager_views.DataRecipientSearchView.as_view(),
        name="line-manager-data-recipient-search",
    ),
    path(
        "line-reports/line-manager-search/",
        line_manager_views.LineReportNewLineManagerSearchView.as_view(),
        name="line-manager-line-report-new-line-manager-search",
    ),
    path(
        "information/",
        line_manager_views.StartView.as_view(),
        name="line-manager-start",
    ),
    path(
        "leaver-cancellation-confirmation/",
        line_manager_views.LeaverCancellationConfirmationView.as_view(),
        name="line-manager-leaver-cancellation-confirmation",
    ),
    path(
        "leaver-cancellation/",
        line_manager_views.LeaverCancellationView.as_view(),
        name="line-manager-leaver-cancellation",
    ),
    path(
        "leaver-confirmation/",
        line_manager_views.LeaverConfirmationView.as_view(),
        name="line-manager-leaver-confirmation",
    ),
    path(
        "leaver-confirmation/remove-data-recipient/",
        line_manager_views.RemoveDataRecipientFromLeavingRequestView.as_view(),
        name="line-manager-remove-data-recipient",
    ),
    path(
        "details/",
        line_manager_views.DetailsView.as_view(),
        name="line-manager-details",
    ),
    path(
        "line-reports/",
        line_manager_views.LeaverLineReportsView.as_view(),
        name="line-manager-leaver-line-reports",
    ),
    path(
        "line-reports/remove-line-manager/",
        line_manager_views.RemoveLineManagerFromLineReportView.as_view(),
        name="remove-line-manager-from-line-report",
    ),
    path(
        "line-reports/" "set-line-manager/<uuid:line_report_uuid>/",
        line_manager_views.line_report_set_new_manager,
        name="line-reports-set-new-manager",
    ),
    path(
        "confirm/",
        line_manager_views.ConfirmDetailsView.as_view(),
        name="line-manager-confirmation",
    ),
    path(
        "thank-you/",
        line_manager_views.ThankYouView.as_view(),
        name="line-manager-thank-you",
    ),
    path(
        "offline-service-now/details/",
        line_manager_views.OfflineServiceNowView.as_view(),
        name="line-manager-offline-service-now-details",
    ),
    path(
        "offline-service-now/thank-you/",
        line_manager_views.OfflineServiceNowThankYouView.as_view(),
        name="line-manager-offline-service-now-thank-you",
    ),
]

leaving_request_sre_urlpatterns = [
    path(
        "",
        sre_views.TaskDetailView.as_view(),
        name="sre-detail",
    ),
    path(
        "service-and-tools/<str:field_name>/edit/",
        sre_views.TaskServiceAndToolsView.as_view(),
        name="sre-service-and-tools",
    ),
    path(
        "service-and-tools/<str:field_name>/read/",
        sre_views.TaskServiceAndToolsViewReadOnly.as_view(),
        name="sre-service-and-tools-read-only",
    ),
    path(
        "confirm/",
        sre_views.TaskCompleteConfirmationView.as_view(),
        name="sre-confirm-complete",
    ),
    path(
        "summary/",
        sre_views.TaskSummaryView.as_view(),
        name="sre-summary",
    ),
    path(
        "thank-you/",
        sre_views.ThankYouView.as_view(),
        name="sre-thank-you",
    ),
]

leaving_request_security_urlpatterns = [
    path(
        "building-pass/",
        security_team_views.BuildingPassConfirmationView.as_view(),
        name="security-team-building-pass-confirmation",
    ),
    path(
        "building-pass/summary/",
        security_team_views.BuildingPassConfirmationReadOnlyView.as_view(),
        name="security-team-building-pass-confirmation-read-only",
    ),
    path(
        "security-clearance/edit/",
        security_team_views.SecurityClearanceConfirmationEditView.as_view(),
        name="security-team-security-clearance-confirmation-edit",
    ),
    path(
        "building-pass/edit/",
        security_team_views.BuildingPassConfirmationEditView.as_view(),
        name="security-team-building-pass-confirmation-edit",
    ),
    path(
        "building-pass/confirm/",
        security_team_views.BuildingPassConfirmationCloseView.as_view(),
        name="security-team-building-pass-confirmation-close",
    ),
    path(
        "rosa-kit/",
        security_team_views.RosaKitConfirmationView.as_view(),
        name="security-team-rosa-kit-confirmation",
    ),
    path(
        "rosa-kit/status/<str:field_name>/",
        security_team_views.RosaKitFieldView.as_view(),
        name="security-team-rosa-kit-field",
    ),
    path(
        "rosa-kit/confirm/",
        security_team_views.RosaKitConfirmationCloseView.as_view(),
        name="security-team-rosa-kit-confirmation-close",
    ),
    path(
        "summary/",
        security_team_views.TaskSummaryView.as_view(),
        name="security-team-summary",
    ),
]


leaving_requests_urlpatterns = [
    path(
        "person-id-error/",
        leaver_views.MultiplePersonIdErrorView.as_view(),
        name="leaver-multiple-person-ids-error",
    ),
    # partial
    path(
        "leaver-search/",
        leaver_views.LeaverSearchView.as_view(),
        name="leaver-leaver-search",
    ),
    # page
    path(
        "select-leaver/",
        leaver_views.SelectLeaverView.as_view(),
        name="leaver-select-leaver",
    ),
    #
    path(
        "",
        common_views.LeavingRequestListView.as_view(show_incomplete=True),
        name="leaving-requests-list",
    ),
    path(
        "complete/",
        common_views.LeavingRequestListView.as_view(show_complete=True),
        name="leaving-requests-list-complete",
    ),
    # Security team
    path(
        "security-team/complete-leaving-request/",
        security_team_views.LeavingRequestListing.as_view(show_complete=True),
        name="security-team-listing-complete",
    ),
    path(
        "security-team/incomplete-leaving-request/",
        security_team_views.LeavingRequestListing.as_view(show_incomplete=True),
        name="security-team-listing-incomplete",
    ),
    # SRE
    path(
        "sre/complete-leaving-request/",
        sre_views.LeavingRequestListing.as_view(show_complete=True),
        name="sre-listing-complete",
    ),
    path(
        "sre/incomplete-leaving-request/",
        sre_views.LeavingRequestListing.as_view(show_incomplete=True),
        name="sre-listing-incomplete",
    ),
]


leaving_request_urlpatterns: list[URLResolver | URLPattern] = [
    path("", common_views.LeavingRequestView.as_view(), name="leaving-request-summary"),
    # partial
    path(
        "already-submitted/",
        leaver_views.LeavingRequestAlreadySubmittedView.as_view(),
        name="leaving-request-already-submitted",
    ),
    path(
        "checks/",
        leaver_views.LeaverChecksView.as_view(),
        name="leaver-checks",
    ),
    path(
        "unable-to-offboard/",
        leaver_views.UnableToOffboardView.as_view(),
        name="unable-to-offboard",
    ),
    path(
        "manager-search/",
        leaver_views.MyManagerSearchView.as_view(),
        name="leaver-manager-search",
    ),
    # page
    path(
        "why-are-you-leaving/",
        leaver_views.WhyAreYouLeavingView.as_view(),
        name="why-are-you-leaving",
    ),
    path(
        "why-are-you-leaving/unhandled-reason/",
        leaver_views.UnhandledLeavingReasonView.as_view(),
        name="leaving-reason-unhandled",
    ),
    path(
        "how-are-you-employed/",
        leaver_views.StaffTypeView.as_view(),
        name="staff-type",
    ),
    path(
        "how-are-you-employed/cannot-use-service/",
        leaver_views.LeaverCannotUseServiceView.as_view(),
        name="cannot-use-service",
    ),
    path(
        "employment-profile/",
        leaver_views.EmploymentProfileView.as_view(),
        name="employment-profile",
    ),
    path(
        "personal-email/",
        leaver_views.LeaverFindDetailsView.as_view(),
        name="leaver-find-details",
    ),
    path(
        "personal-email-help/",
        leaver_views.LeaverFindDetailsHelpView.as_view(),
        name="leaver-find-details-help",
    ),
    path(
        "leaver-dates/remove-line-manager/",
        leaver_views.RemoveLineManagerFromLeavingRequestView.as_view(),
        name="leaver-remove-line-manager",
    ),
    path(
        "leaver-dates/",
        leaver_views.LeaverDatesView.as_view(),
        name="leaver-dates",
    ),
    path(
        "health-and-safety-or-floor-liaison-officer/",
        leaver_views.HSFLOfficerView.as_view(),
        name="hsfl-officer",
    ),
    path(
        "leaver-assets/",
        leaver_views.LeaverHasAssetsView.as_view(),
        name="leaver-has-assets",
    ),
    path(
        "has-cirrus-equipment/",
        leaver_views.HasCirrusEquipmentView.as_view(),
        name="leaver-has-cirrus-equipment",
    ),
    path(
        "cirrus-equipment/",
        leaver_views.CirrusEquipmentView.as_view(),
        name="leaver-cirrus-equipment",
    ),
    path(
        "cirrus-equipment/delete/<uuid:kit_uuid>",
        leaver_views.DeleteCirrusEquipmentView.as_view(),
        name="leaver-cirrus-equipment-delete",
    ),
    path(
        "display-screen-equipment/",
        leaver_views.DisplayScreenEquipmentView.as_view(),
        name="leaver-display-screen-equipment",
    ),
    path(
        "display-screen-equipment/delete/<uuid:kit_uuid>",
        leaver_views.DeleteDSEView.as_view(),
        name="leaver-display-screen-equipment-delete",
    ),
    path(
        "contact-details/",
        leaver_views.LeaverContactDetailsView.as_view(),
        name="leaver-contact-details",
    ),
    path(
        "confirm-details/",
        leaver_views.ConfirmDetailsView.as_view(),
        name="leaver-confirm-details",
    ),
    path(
        "request-received/",
        leaver_views.RequestReceivedView.as_view(),
        name="leaver-request-received",
    ),
    path("review/", include(leaving_request_review_urlpatterns)),
    path("security/", include(leaving_request_security_urlpatterns)),
    path("sre/", include(leaving_request_sre_urlpatterns)),
]

admin_urlpatterns = [
    path(
        "",
        admin_views.LeaversAdminView.as_view(),
        name="leavers-admin",
    ),
    path(
        "servicenow-offline/",
        admin_views.OfflineServiceNowAdmin.as_view(),
        name="leavers-servicenow-admin",
    ),
    path(
        "leaving-requests/",
        admin_views.LeavingRequestListingView.as_view(),
        name="admin-leaving-request-listing",
    ),
    path(
        "leaving-requests/<uuid:leaving_request_uuid>/",
        admin_views.LeavingRequestDetailView.as_view(),
        name="admin-leaving-request-detail",
    ),
    path(
        "leaving-requests/<uuid:leaving_request_uuid>/manually-offboard-uksbs/",
        admin_views.LeavingRequestManuallyOffboarded.as_view(),
        name="admin-leaving-request-manually-offboard-uksbs",
    ),
]

workflow_urlpatterns = [
    path(
        "",
        workflow_urls(
            view=flow_views.LeaversFlowView,
            list_view=flow_views.LeaversFlowListView,
            create_view=flow_views.LeaversFlowCreateView,
            continue_view=flow_views.LeaversFlowContinueView,
        ),
    ),
]

# Redirect URL to new URL name.
redirect_mapping: Dict[str, str] = {
    "line-manager/uuid:leaving_request_uuid/information/": "line-manager-start",
    "line-manager/uuid:leaving_request_uuid/thank-you/": "line-manager-thank-you",
    "line-manager/uuid:leaving_request_uuid/offline-service-now/details/": (
        "line-manager-offline-service-now-details"
    ),
    "leaver/security-team/uuid:leaving_request_uuid/building-pass/": (
        "security-team-building-pass-confirmation"
    ),
    "leaver/security-team/uuid:leaving_request_uuid/rosa-kit/": (
        "security-team-rosa-kit-confirmation"
    ),
    "leaver/sre/uuid:leaving_request_uuid/": "sre-detail",
}

redirect_urlpatterns = [
    path(p, RedirectView.as_view(pattern_name=new_name))
    for p, new_name in redirect_mapping.items()
]

urlpatterns = redirect_urlpatterns + [
    path("", RedirectView.as_view(url=reverse_lazy("start")), name="leavers-root"),
    path("start/", leaver_views.LeaversStartView.as_view(), name="start"),
    path(
        "who-is-leaving/",
        leaver_views.WhoIsLeavingView.as_view(),
        name="who-is-leaving",
    ),
    path(
        "someone-else-is-leaving/",
        leaver_views.SomeoneElseIsLeavingErrorView.as_view(),
        name="someone-else-is-leaving-error",
    ),
    # leaving request
    path("leaving-requests/", include(leaving_requests_urlpatterns)),
    path(
        "leaving-requests/<uuid:leaving_request_uuid>/",
        include(leaving_request_urlpatterns),
    ),
    # admin
    path("admin/", include(admin_urlpatterns)),
    # workflow
    path("leaving-workflow/", include(workflow_urlpatterns)),
]
