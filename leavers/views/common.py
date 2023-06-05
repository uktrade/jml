from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, TypedDict, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse, reverse_lazy

from core.utils.helpers import make_possessive
from core.utils.staff_index import get_staff_document_from_staff_index
from core.views import BaseTemplateView
from leavers.forms.data_processor import HRLeavingRequestListingSearchForm
from leavers.models import LeaverInformation, LeavingRequest
from leavers.utils.leaving_request import initialise_line_reports
from leavers.views.base import LeavingRequestListing, LeavingRequestViewMixin
from leavers.views.leaver import LeavingJourneyViewMixin
from leavers.views.line_manager import ReviewViewMixin

if TYPE_CHECKING:
    from user.models import User
else:
    User = get_user_model()


class LeavingRequestListView(UserPassesTestMixin, LeavingRequestListing):
    template_name = "leaving/common/leaving_request_list.html"
    form_class = HRLeavingRequestListingSearchForm

    complete_field = "line_manager_complete"
    # These views will contain the task list for HR to complete/review what was done
    confirmation_view = "leaving-request-summary"
    summary_view = "leaving-request-summary"
    fields: List[Tuple[str, str]] = [
        ("leaver_name", "Leaver's name"),
        ("leaving_date", "Leaving date"),
        ("last_working_day", "Last working day"),
        ("complete", "Status"),
    ]

    def test_func(self) -> Optional[bool]:
        user = cast(User, self.request.user)
        return user.has_perm("leavers.select_leaver")

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(full_width=True)
        return form_kwargs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            offboard_url=reverse("leaver-select-leaver"),
        )
        return context


class StepStatus(TypedDict):
    url: str
    status: str
    view_name: str
    previous_step_complete: bool


class LeavingRequestView(
    UserPassesTestMixin, BaseTemplateView, LeavingRequestViewMixin
):
    template_name = "leaving/common/leaving_request.html"
    back_link_url = reverse_lazy("leaving-requests-list")

    def test_func(self) -> Optional[bool]:
        user = cast(User, self.request.user)
        return user.has_perm("leavers.select_leaver")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name = make_possessive(leaver_name)

        staff_document = get_staff_document_from_staff_index(
            sso_email_user_id=self.leaving_request.leaver_activitystream_user.email_user_id,
        )

        leaver_step_statuses, manager_step_statuses = self.get_step_statuses()

        context.update(
            page_title=f"{possessive_leaver_name} leaving request",
            leaving_request=self.leaving_request,
            staff_uuid=staff_document.uuid,
            leaver_step_statuses=leaver_step_statuses,
            manager_step_statuses=manager_step_statuses,
        )

        return context

    def get_step_status(
        self,
        lr: LeavingRequest,
        li: LeaverInformation,
        step_data_mapping: Dict[Any, Any],
        step_pathname: str,
        step: Dict[Any, Any],
        previous_step_complete: bool,
    ) -> Optional[StepStatus]:
        if not step["show_in_summary"]:
            return None

        step_data = step_data_mapping[step_pathname]
        step_url = reverse(
            step_pathname,
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )

        step_status_data: StepStatus = {
            "url": step_url,
            "status": "not started",
            "view_name": step["view_name"],
            "previous_step_complete": previous_step_complete,
        }

        if lr.line_manager_complete:
            step_status_data["status"] = "complete"
            return step_status_data

        if all(step_data):
            step_status_data["status"] = "complete"
        elif any(step_data):
            step_status_data["status"] = "started"

        if (
            "leaver-has-cirrus-equipment" in step_pathname
            and li.has_cirrus_kit is not None
            and li.has_cirrus_kit is False
        ):
            step_status_data["status"] = "complete"
        if (
            "leaver-display-screen-equipment" in step_pathname
            and li.has_dse is not None
            and not li.has_dse
        ):
            return None
        if (
            "line-manager-leaver-line-reports" in step_pathname
            and not lr.show_hr_and_payroll
        ):
            return None
        if (
            "line-manager-leaver-line-reports" in step_pathname
            and not lr.show_line_reports
            and not lr.line_reports
        ):
            return None

        if not previous_step_complete:
            step_status_data["status"] = "cannot start yet"

        return step_status_data

    def get_step_statuses(self) -> Tuple[List[StepStatus], List[StepStatus]]:
        leaver_step_statuses = []
        manager_step_statuses = []

        lr = self.leaving_request
        li = self.leaving_request.leaver_information.first()
        assert li

        if lr.line_reports is None:
            initialise_line_reports(leaving_request=lr)
        line_reports = lr.line_reports

        step_data_mapping = {
            "why-are-you-leaving": [
                lr.reason_for_leaving,
            ],
            "staff-type": [
                lr.staff_type,
            ],
            "employment-profile": [
                li.leaver_first_name,
                li.leaver_last_name,
                li.leaver_date_of_birth,
                li.job_title,
                lr.security_clearance,
            ],
            "leaver-dates": [
                li.leaving_date,
                li.last_day,
                lr.manager_activitystream_user,
            ],
            "hsfl-officer": [
                li.is_health_and_safety_officer is not None,
                li.is_floor_liaison_officer is not None,
            ],
            "leaver-has-assets": [
                lr.holds_government_procurement_card is not None,
                lr.is_rosa_user is not None,
                li.has_dse is not None,
            ],
            "leaver-has-cirrus-equipment": [
                li.cirrus_assets is not None,
                li.return_option,
                li.return_personal_phone,
                li.return_contact_email,
            ],
            "leaver-display-screen-equipment": [
                li.has_dse is not None,
                not li.has_dse or li.dse_assets,
            ],
            "leaver-contact-details": [
                li.contact_phone,
                li.personal_email,
                li.contact_address_line_1,
                li.contact_address_city,
                li.contact_address_county,
                li.contact_address_postcode,
            ],
            "leaver-confirm-details": [
                lr.leaver_complete,
            ],
            "line-manager-leaver-confirmation": [
                lr.last_day,
                lr.leaving_date,
            ],
            "line-manager-details": [
                lr.leaver_paid_unpaid,
                lr.annual_leave,
                lr.flexi_leave,
            ],
            "line-manager-leaver-line-reports": [
                bool(lr["line_manager"]) for lr in line_reports
            ],
            "line-manager-confirmation": [
                lr.line_manager_complete,
            ],
        }

        previous_step_complete = True
        for step_pathname, step in LeavingJourneyViewMixin.JOURNEY.items():
            step_status = self.get_step_status(
                lr=lr,
                li=li,
                step_data_mapping=step_data_mapping,
                step_pathname=step_pathname,
                step=step,
                previous_step_complete=previous_step_complete,
            )

            if step_status is None:
                continue

            leaver_step_statuses.append(step_status)
            if step_status["status"] != "complete":
                previous_step_complete = False

        for step_pathname, step in ReviewViewMixin.JOURNEY.items():
            step_status = self.get_step_status(
                lr=lr,
                li=li,
                step_data_mapping=step_data_mapping,
                step_pathname=step_pathname,
                step=step,
                previous_step_complete=previous_step_complete,
            )

            if step_status is None:
                continue

            manager_step_statuses.append(step_status)
            if step_status["status"] != "complete":
                previous_step_complete = False

        return leaver_step_statuses, manager_step_statuses
