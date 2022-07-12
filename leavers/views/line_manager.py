from typing import Any, Dict, List, Optional, Tuple, cast
from uuid import UUID, uuid4

from django.http import (
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseRedirect,
)
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from activity_stream.models import ActivityStreamStaffSSOUser
from core.staff_search.views import StaffSearchView
from core.uksbs import get_uksbs_interface
from core.uksbs.types import PersonData, PersonHierarchyData
from core.utils.helpers import make_possessive
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    StaffDocument,
    consolidate_staff_documents,
    get_staff_document_from_staff_index,
)
from leavers.forms import line_manager as line_manager_forms
from leavers.models import LeaverInformation, LeavingRequest
from leavers.progress_indicator import ProgressIndicator
from user.models import User

DATA_RECIPIENT_SEARCH_PARAM = "data_recipient_id"
NEW_LINE_REPORT_SEARCH_PARAM = "new_line_report_id"
LINE_REPORT_NEW_LINE_MANAGER_SEARCH_PARAM = "new_line_manager_id"


class LineManagerProgressIndicator(ProgressIndicator):

    steps: List[Tuple[str, str, str]] = [
        ("leaver_details", "Leaver's details", "line-manager-leaver-confirmation"),
        ("hr_payroll", "HR and payroll", "line-manager-details"),
        ("line_reports", "Leaver's line reports", "line-manager-leaver-line-reports"),
        ("confirmation", "Confirmation", "line-manager-confirmation"),
    ]

    def __init__(self, current_step: str, leaving_request_uuid: str) -> None:
        super().__init__(current_step)
        self.leaving_request_uuid = leaving_request_uuid

    def get_step_link(self, step) -> str:
        return reverse_lazy(
            step[2],
            kwargs={"leaving_request_uuid": self.leaving_request_uuid},
        )


class LineManagerViewMixin:
    def line_manager_access(
        self,
        request: HttpRequest,
        leaving_request: LeavingRequest,
    ) -> bool:
        user = cast(User, request.user)
        manager_activitystream_user = leaving_request.manager_activitystream_user

        # Check if we know the line manager
        if not manager_activitystream_user:
            return False

        # Check if the user viewing the page is the Line manager
        if user.sso_email_user_id != manager_activitystream_user.email_user_id:
            return False

        return True


class DataRecipientSearchView(LineManagerViewMixin, StaffSearchView):
    search_name = "data recipient"
    query_param_name = DATA_RECIPIENT_SEARCH_PARAM

    def get_success_url(self) -> str:
        return reverse(
            "line-manager-leaver-confirmation",
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        self.leaving_request = get_object_or_404(
            LeavingRequest, uuid=kwargs["leaving_request_uuid"]
        )

        if self.leaving_request.line_manager_complete:
            return redirect(
                reverse(
                    "line-manager-thank-you",
                    kwargs={"leaving_request_uuid": self.leaving_request.uuid},
                )
            )

        if not self.line_manager_access(
            request=request,
            leaving_request=self.leaving_request,
        ):
            return HttpResponseForbidden()

        self.exclude_staff_ids = [
            self.leaving_request.leaver_activitystream_user.identifier
        ]
        return super().dispatch(request, *args, **kwargs)


class NewLineReportSearchView(LineManagerViewMixin, StaffSearchView):
    search_name = "missing line report"
    query_param_name = NEW_LINE_REPORT_SEARCH_PARAM

    def get_success_url(self) -> str:
        return reverse(
            "add-missing-line-report",
            kwargs={
                "leaving_request_uuid": self.leaving_request.uuid,
            },
        )

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        self.leaving_request = get_object_or_404(
            LeavingRequest, uuid=kwargs["leaving_request_uuid"]
        )

        if self.leaving_request.line_manager_complete:
            return redirect(
                reverse(
                    "line-manager-thank-you",
                    kwargs={"leaving_request_uuid": self.leaving_request.uuid},
                )
            )

        if not self.line_manager_access(
            request=request,
            leaving_request=self.leaving_request,
        ):
            return HttpResponseForbidden()

        self.exclude_staff_ids = [
            self.leaving_request.leaver_activitystream_user.identifier
        ]

        # TODO: Fix so that you can't accidentally set the new line manager to
        # be the same as the line report.
        # for line_report in self.leaving_request.line_reports:
        #     try:
        #         line_report_as_user = ActivityStreamStaffSSOUser.objects.get(
        #             email_address=line_report["email"]
        #         )
        #     except ActivityStreamStaffSSOUser.DoesNotExist:
        #         continue

        #     self.exclude_staff_ids.append(line_report_as_user.identifier)

        return super().dispatch(request, *args, **kwargs)


class LineReportNewLineManagerSearchView(LineManagerViewMixin, StaffSearchView):
    search_name = "new line manager"
    query_param_name = LINE_REPORT_NEW_LINE_MANAGER_SEARCH_PARAM

    def get_success_url(self) -> str:

        return reverse(
            "line-reports-set-new-manager",
            kwargs={
                "leaving_request_uuid": self.leaving_request.uuid,
                "line_report_uuid": self.request.GET["line_report_uuid"],
            },
        )

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        self.leaving_request = get_object_or_404(
            LeavingRequest, uuid=kwargs["leaving_request_uuid"]
        )

        if self.leaving_request.line_manager_complete:
            return redirect(
                reverse(
                    "line-manager-thank-you",
                    kwargs={"leaving_request_uuid": self.leaving_request.uuid},
                )
            )

        if not self.line_manager_access(
            request=request,
            leaving_request=self.leaving_request,
        ):
            return HttpResponseForbidden()

        self.exclude_staff_ids = [
            self.leaving_request.leaver_activitystream_user.identifier
        ]

        # line_report_uuid = self.request.GET["line_report_uuid"]

        # TODO: Fix so that you can't accidentally set the new line manager to
        # be the same as the line report.
        # for line_report in self.leaving_request.line_reports:
        #     if line_report["uuid"] == line_report_uuid:
        #         try:
        #             line_report_as_user = ActivityStreamStaffSSOUser.objects.get(
        #                 email_address=line_report["email"]
        #             )
        #         except ActivityStreamStaffSSOUser.DoesNotExist:
        #             continue
        #         self.exclude_staff_ids.append(line_report_as_user.identifier)

        return super().dispatch(request, *args, **kwargs)


class StartView(LineManagerViewMixin, TemplateView):
    template_name = "leaving/line_manager/start.html"

    def dispatch(self, request, *args, **kwargs):
        self.leaving_request = get_object_or_404(
            LeavingRequest, uuid=kwargs["leaving_request_uuid"]
        )

        if self.leaving_request.line_manager_complete:
            return redirect(
                reverse(
                    "line-manager-thank-you",
                    kwargs={"leaving_request_uuid": self.leaving_request.uuid},
                )
            )

        if not self.line_manager_access(
            request=request,
            leaving_request=self.leaving_request,
        ):
            return HttpResponseForbidden()

        if not self.leaving_request.leaver_complete:
            return HttpResponseNotFound()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()

        context.update(
            page_title="Leaving DIT: line manager's off-boarding actions",
            start_url=reverse(
                "line-manager-leaver-confirmation",
                kwargs={"leaving_request_uuid": str(self.leaving_request.uuid)},
            ),
            leaver_name=leaver_name,
            possessive_leaver_name=make_possessive(leaver_name),
        )

        return context


class LeaverConfirmationView(LineManagerViewMixin, FormView):
    template_name = "leaving/line_manager/leaver_confirmation.html"
    form_class = line_manager_forms.ConfirmLeavingDate

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(
            leaver=self.get_leaver(),
        )
        return form_kwargs

    def get_success_url(self) -> str:
        return reverse(
            "line-manager-details",
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )

    def get_leaver(self) -> ConsolidatedStaffDocument:
        """
        Get the Leaver StaffDocument
        """
        # Load the leaver from the Staff index.
        leaver_staff_document: StaffDocument = get_staff_document_from_staff_index(
            sso_email_user_id=self.leaving_request.leaver_activitystream_user.email_user_id,
        )
        return consolidate_staff_documents(
            staff_documents=[leaver_staff_document],
        )[0]

    def get_manager(self) -> ConsolidatedStaffDocument:
        """
        Get the Manager StaffDocument
        """
        # Load the line manager from the Staff index.
        manager_staff_document: StaffDocument = get_staff_document_from_staff_index(
            sso_email_user_id=self.leaving_request.manager_activitystream_user.email_user_id,
        )
        return consolidate_staff_documents(
            staff_documents=[manager_staff_document],
        )[0]

    def get_data_recipient(self, request):
        """
        Gets the Data recipient from the DB or the GET param.

        Sets the following values:
        - self.data_recipient
        - self.data_recipient_activitystream_user
        """

        data_recipient_uuid: Optional[str] = request.GET.get(
            DATA_RECIPIENT_SEARCH_PARAM, None
        )
        data_recipient_staff_document: Optional[StaffDocument] = None

        # Try to load the data recipient using existing data from the database.
        if (
            not data_recipient_uuid
            and self.leaving_request.data_recipient_activitystream_user
        ):
            self.data_recipient_activitystream_user = (
                self.leaving_request.data_recipient_activitystream_user
            )
            data_recipient_staff_document: StaffDocument = get_staff_document_from_staff_index(
                sso_email_user_id=(
                    self.leaving_request.data_recipient_activitystream_user.email_user_id
                ),
            )

        # Load the data recipient from the Staff index.
        if data_recipient_uuid and not data_recipient_staff_document:
            data_recipient_staff_document: StaffDocument = (
                get_staff_document_from_staff_index(staff_uuid=data_recipient_uuid)
            )

        # If we have a data recipient, we can create a ConsolidatedStaffDocument and
        # store data in the session.
        if data_recipient_staff_document:
            self.data_recipient: ConsolidatedStaffDocument = (
                consolidate_staff_documents(
                    staff_documents=[data_recipient_staff_document],
                )[0]
            )
            try:
                self.data_recipient_activitystream_user = (
                    ActivityStreamStaffSSOUser.objects.get(
                        identifier=self.data_recipient["staff_sso_activity_stream_id"],
                    )
                )
            except ActivityStreamStaffSSOUser.DoesNotExist:
                raise Exception(
                    "Unable to find data recipient in the Staff SSO ActivityStream."
                )

        # Store data recipient against the LeavingRequest.
        self.leaving_request.data_recipient_activitystream_user = (
            self.data_recipient_activitystream_user
        )
        self.leaving_request.save()

    def dispatch(self, request, *args, **kwargs):
        self.leaving_request = get_object_or_404(
            LeavingRequest, uuid=kwargs["leaving_request_uuid"]
        )
        self.progress_indicator = LineManagerProgressIndicator(
            current_step="leaver_details",
            leaving_request_uuid=self.leaving_request.uuid,
        )

        if self.leaving_request.line_manager_complete:
            return redirect(
                reverse(
                    "line-manager-thank-you",
                    kwargs={"leaving_request_uuid": self.leaving_request.uuid},
                )
            )

        if not self.line_manager_access(
            request=request,
            leaving_request=self.leaving_request,
        ):
            return HttpResponseForbidden()

        if not self.leaving_request.leaver_complete:
            return HttpResponseNotFound()

        self.leaver: ConsolidatedStaffDocument = self.get_leaver()
        self.manager: ConsolidatedStaffDocument = self.get_manager()

        self.data_recipient: Optional[ConsolidatedStaffDocument] = None
        self.data_recipient_activitystream_user: Optional[
            ActivityStreamStaffSSOUser
        ] = None
        self.get_data_recipient(request)

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        leaver_information: Optional[
            LeaverInformation
        ] = self.leaving_request.leaver_information.first()

        if self.leaving_request.last_day:
            initial["last_day"] = self.leaving_request.last_day
        elif leaver_information and leaver_information.last_day:
            initial["last_day"] = leaver_information.last_day
        if self.leaving_request.leaving_date:
            initial["leaving_date"] = self.leaving_request.leaving_date
        elif leaver_information and leaver_information.leaving_date:
            initial["leaving_date"] = leaver_information.leaving_date
        if self.leaving_request.reason_for_leaving:
            initial["reason_for_leaving"] = self.leaving_request.reason_for_leaving
        return initial

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:

        context = super().get_context_data(**kwargs)

        leaver_name = f"{self.leaver['first_name']} {self.leaver['last_name']}"
        possessive_leaver_name = make_possessive(leaver_name)

        context.update(
            page_title=f"{possessive_leaver_name} details",
            leaver=self.leaver,
            leaver_name=leaver_name,
            possessive_leaver_name=possessive_leaver_name,
            data_recipient=self.data_recipient or self.manager,
            data_recipient_search=reverse(
                "line-manager-data-recipient-search",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
            progress_steps=self.progress_indicator.get_progress_steps(),
        )
        return context

    def form_valid(self, form) -> HttpResponse:
        # If there is no data recipient set, we set the recipient as the manager.
        if not self.data_recipient:
            self.leaving_request.data_recipient_activitystream_user = (
                self.leaving_request.manager_activitystream_user
            )

        # Store the leaving date against the LeavingRequest.
        self.leaving_request.last_day = form.cleaned_data["last_day"]
        self.leaving_request.leaving_date = form.cleaned_data["leaving_date"]
        self.leaving_request.reason_for_leaving = form.cleaned_data[
            "reason_for_leaving"
        ]
        self.leaving_request.save()

        return super().form_valid(form)


class DetailsView(LineManagerViewMixin, FormView):
    template_name = "leaving/line_manager/details.html"
    form_class = line_manager_forms.LineManagerDetailsForm

    def get_success_url(self) -> str:
        return reverse(
            "line-manager-leaver-line-reports",
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        initial.update(
            leaver_paid_unpaid=self.leaving_request.leaver_paid_unpaid,
            annual_leave=self.leaving_request.annual_leave,
            annual_leave_measurement=self.leaving_request.annual_leave_measurement,
            flexi_leave=self.leaving_request.flexi_leave,
            annual_number=self.leaving_request.annual_number,
            flexi_number=self.leaving_request.flexi_number,
        )
        return initial

    def dispatch(self, request, *args, **kwargs):
        self.leaving_request = get_object_or_404(
            LeavingRequest, uuid=kwargs["leaving_request_uuid"]
        )
        self.progress_indicator = LineManagerProgressIndicator(
            current_step="hr_payroll",
            leaving_request_uuid=self.leaving_request.uuid,
        )

        if self.leaving_request.line_manager_complete:
            return redirect(
                reverse(
                    "line-manager-thank-you",
                    kwargs={"leaving_request_uuid": self.leaving_request.uuid},
                )
            )

        if not self.line_manager_access(
            request=request,
            leaving_request=self.leaving_request,
        ):
            return HttpResponseForbidden()

        if not self.leaving_request.leaver_complete:
            return HttpResponseNotFound()

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(leaver_name=self.leaving_request.get_leaver_name())
        return form_kwargs

    def form_valid(self, form) -> HttpResponse:
        # Store the details against the LeavingRequest.
        self.leaving_request.leaver_paid_unpaid = form.cleaned_data[
            "leaver_paid_unpaid"
        ]
        self.leaving_request.annual_leave = form.cleaned_data["annual_leave"]
        self.leaving_request.annual_leave_measurement = form.cleaned_data[
            "annual_leave_measurement"
        ]
        self.leaving_request.flexi_leave = form.cleaned_data["flexi_leave"]

        if form.cleaned_data["annual_number"]:
            self.leaving_request.annual_number = float(
                form.cleaned_data["annual_number"]
            )
        if form.cleaned_data["flexi_number"]:
            self.leaving_request.flexi_number = float(form.cleaned_data["flexi_number"])
        self.leaving_request.save()

        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(
            page_title="HR and payroll",
            leaver_name=self.leaving_request.get_leaver_name(),
            progress_steps=self.progress_indicator.get_progress_steps(),
        )

        return context


def add_missing_line_report(
    request: HttpRequest, leaving_request_uuid: UUID
) -> HttpResponse:
    leaving_request = get_object_or_404(LeavingRequest, uuid=leaving_request_uuid)
    if leaving_request.line_manager_complete:
        return redirect(
            reverse(
                "line-manager-thank-you",
                kwargs={"leaving_request_uuid": leaving_request_uuid},
            )
        )

    if not leaving_request.leaver_complete:
        return HttpResponseNotFound()

    redirect_response = HttpResponseRedirect(
        reverse(
            "line-manager-leaver-line-reports",
            kwargs={"leaving_request_uuid": leaving_request_uuid},
        )
    )

    line_reports: List[Dict[str, Any]] = leaving_request.line_reports

    new_line_report_staff_id: Optional[str] = request.GET.get(
        NEW_LINE_REPORT_SEARCH_PARAM
    )
    if new_line_report_staff_id:
        new_line_report_staff_document: StaffDocument = (
            get_staff_document_from_staff_index(staff_uuid=new_line_report_staff_id)
        )
        consolidated_staff_document: ConsolidatedStaffDocument = (
            consolidate_staff_documents(
                staff_documents=[new_line_report_staff_document],
            )[0]
        )

        line_report_email: str = consolidated_staff_document["email_addresses"][0]

        # Check if the line report already exists.
        for line_report in line_reports:
            if line_report["email"] == line_report_email:
                return redirect_response

        line_report_name: str = (
            consolidated_staff_document["first_name"]
            + " "
            + consolidated_staff_document["last_name"]
        )

        # Create a new line report
        new_line_report: Dict[str, Any] = {
            "uuid": str(uuid4()),
            "name": line_report_name,
            "email": line_report_email,
            "line_manager": None,
            "new_line_report": True,
        }
        line_reports.append(new_line_report)
        leaving_request.line_reports = line_reports
        leaving_request.save()

    return redirect_response


def line_report_set_new_manager(
    request: HttpRequest, leaving_request_uuid: UUID, line_report_uuid: UUID
) -> HttpResponse:
    leaving_request = get_object_or_404(LeavingRequest, uuid=leaving_request_uuid)
    if leaving_request.line_manager_complete:
        return redirect(
            reverse(
                "line-manager-thank-you",
                kwargs={"leaving_request_uuid": leaving_request_uuid},
            )
        )

    if not leaving_request.leaver_complete:
        return HttpResponseNotFound()

    line_reports: List[Dict[str, Any]] = leaving_request.line_reports

    line_manager_staff_id: Optional[str] = request.GET.get(
        LINE_REPORT_NEW_LINE_MANAGER_SEARCH_PARAM
    )
    if line_manager_staff_id:
        line_manager_staff_document: StaffDocument = (
            get_staff_document_from_staff_index(staff_uuid=line_manager_staff_id)
        )
        consolidated_staff_document: ConsolidatedStaffDocument = (
            consolidate_staff_documents(
                staff_documents=[line_manager_staff_document],
            )[0]
        )
        line_manager_name = (
            consolidated_staff_document["first_name"]
            + " "
            + consolidated_staff_document["last_name"]
        )
        line_manager_email = consolidated_staff_document["email_addresses"][0]
        for line_report in line_reports:
            if line_report["uuid"] == str(line_report_uuid):
                line_report["line_manager"] = {
                    "name": line_manager_name,
                    "email": line_manager_email,
                }
                break
        leaving_request.line_reports = line_reports
        leaving_request.save()

    return HttpResponseRedirect(
        reverse(
            "line-manager-leaver-line-reports",
            kwargs={"leaving_request_uuid": leaving_request_uuid},
        )
    )


class LeaverLineReportsView(LineManagerViewMixin, FormView):
    template_name = "leaving/line_manager/line_reports.html"
    form_class = line_manager_forms.LineReportConfirmationForm

    def get_success_url(self) -> str:
        return reverse(
            "line-manager-confirmation",
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )

    def initialize_line_reports(self) -> None:
        if not self.leaving_request.line_reports:
            uksbs_interface = get_uksbs_interface()
            leaver_hierarchy_data: PersonHierarchyData = (
                uksbs_interface.get_user_hierarchy(
                    oracle_id=self.leaving_request.leaver_activitystream_user.user_id,
                )
            )
            person_data_line_reports: List[PersonData] = leaver_hierarchy_data.get(
                "report", []
            )

            line_reports: List[Dict[str, Any]] = [
                {
                    "uuid": str(uuid4()),
                    "name": line_report["full_name"],
                    "email": line_report["email_address"],
                    "line_manager": None,
                    "person_data": line_report,
                    "new_line_report": False,
                }
                for line_report in person_data_line_reports
            ]
            self.leaving_request.line_reports = line_reports
            self.leaving_request.save()

    def dispatch(self, request, *args, **kwargs):
        self.leaving_request = get_object_or_404(
            LeavingRequest, uuid=kwargs["leaving_request_uuid"]
        )
        self.progress_indicator = LineManagerProgressIndicator(
            current_step="line_reports",
            leaving_request_uuid=self.leaving_request.uuid,
        )

        if self.leaving_request.line_manager_complete:
            return redirect(
                reverse(
                    "line-manager-thank-you",
                    kwargs={"leaving_request_uuid": self.leaving_request.uuid},
                )
            )

        if not self.line_manager_access(
            request=request,
            leaving_request=self.leaving_request,
        ):
            return HttpResponseForbidden()

        if not self.leaving_request.leaver_complete:
            return HttpResponseNotFound()

        self.initialize_line_reports()

        if not self.leaving_request.line_reports:
            return self.get_success_url()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(
            page_title="Leaver's line reports",
            leaver_name=self.leaving_request.get_leaver_name(),
            progress_steps=self.progress_indicator.get_progress_steps(),
            line_reports=self.leaving_request.line_reports,
            new_line_manager_search=reverse(
                "line-manager-line-report-new-line-manager-search",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
            new_line_report_search=reverse(
                "line-manager-new-line-report-search",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
        )

        return context

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs["leaving_request"] = self.leaving_request
        return form_kwargs


class ConfirmDetailsView(LineManagerViewMixin, FormView):
    template_name = "leaving/line_manager/confirm_details.html"
    form_class = line_manager_forms.LineManagerConfirmationForm

    def get_success_url(self) -> str:
        return reverse(
            "line-manager-thank-you",
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )

    def get_leaver(self) -> ConsolidatedStaffDocument:
        """
        Get the Leaver StaffDocument
        """
        # Load the leaver from the Staff index.
        leaver_staff_document: StaffDocument = get_staff_document_from_staff_index(
            sso_email_user_id=self.leaving_request.leaver_activitystream_user.email_user_id,
        )
        return consolidate_staff_documents(
            staff_documents=[leaver_staff_document],
        )[0]

    def get_data_recipient(self) -> ConsolidatedStaffDocument:
        """
        Get the Data Recipient StaffDocument
        """
        # Load the Data Recipient from the Staff index.
        data_recipient_staff_document: StaffDocument = get_staff_document_from_staff_index(
            sso_email_user_id=self.leaving_request.data_recipient_activitystream_user.email_user_id,
        )
        return consolidate_staff_documents(
            staff_documents=[data_recipient_staff_document],
        )[0]

    def dispatch(self, request, *args, **kwargs):
        self.leaving_request = get_object_or_404(
            LeavingRequest, uuid=kwargs["leaving_request_uuid"]
        )
        self.progress_indicator = LineManagerProgressIndicator(
            current_step="confirmation",
            leaving_request_uuid=self.leaving_request.uuid,
        )

        if self.leaving_request.line_manager_complete:
            return redirect(
                reverse(
                    "line-manager-thank-you",
                    kwargs={"leaving_request_uuid": self.leaving_request.uuid},
                )
            )

        if not self.line_manager_access(
            request=request,
            leaving_request=self.leaving_request,
        ):
            return HttpResponseForbidden()

        if not self.leaving_request.leaver_complete:
            return HttpResponseNotFound()

        self.leaver: ConsolidatedStaffDocument = self.get_leaver()
        self.data_recipient: ConsolidatedStaffDocument = self.get_data_recipient()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name = make_possessive(leaver_name)

        reason_for_leaving: Optional[str] = None
        if self.leaving_request.reason_for_leaving:
            reason_for_leaving = line_manager_forms.ReasonForleaving(
                self.leaving_request.reason_for_leaving
            ).label

        annual_leave: Optional[str] = None
        if self.leaving_request.annual_leave:
            annual_leave_enum = line_manager_forms.AnnualLeavePaidOrDeducted(
                self.leaving_request.annual_leave
            )
            annual_leave = annual_leave_enum.label
        has_annual_leave = bool(annual_leave_enum.value != "None")

        annual_leave_measurement: Optional[str] = None
        if self.leaving_request.annual_leave_measurement:
            annual_leave_measurement = line_manager_forms.DaysHours(
                self.leaving_request.annual_leave_measurement
            ).label

        flexi_leave: Optional[str] = None
        if self.leaving_request.flexi_leave:
            flexi_leave_enum = line_manager_forms.FlexiLeavePaidOrDeducted(
                self.leaving_request.flexi_leave
            )
            flexi_leave = flexi_leave_enum.label
        has_flexi_leave = bool(flexi_leave_enum.value != "None")

        context.update(
            page_title="Confirm all the information",
            progress_steps=self.progress_indicator.get_progress_steps(),
            leaver_name=leaver_name,
            possessive_leaver_name=possessive_leaver_name,
            leaver=self.leaver,
            data_recipient=self.data_recipient,
            last_day=self.leaving_request.last_day.date(),
            leaving_date=self.leaving_request.leaving_date.date(),
            reason_for_leaving=reason_for_leaving,
            annual_leave=annual_leave,
            has_annual_leave=has_annual_leave,
            annual_leave_measurement=annual_leave_measurement,
            annual_number=self.leaving_request.annual_number,
            flexi_leave=flexi_leave,
            has_flexi_leave=has_flexi_leave,
            flexi_number=self.leaving_request.flexi_number,
            line_reports=self.leaving_request.line_reports,
            leaver_confirmation_view_url=reverse_lazy(
                "line-manager-leaver-confirmation",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
            details_view_url=reverse_lazy(
                "line-manager-details",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
            line_reports_view=reverse_lazy(
                "line-manager-leaver-line-reports",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
        )

        return context

    def form_valid(self, form) -> HttpResponse:
        self.leaving_request.line_manager_complete = timezone.now()
        self.leaving_request.save()

        return super().form_valid(form)


class ThankYouView(LineManagerViewMixin, TemplateView):
    template_name = "leaving/line_manager/thank_you.html"

    def dispatch(self, request, *args, **kwargs):
        self.leaving_request = get_object_or_404(
            LeavingRequest, uuid=kwargs["leaving_request_uuid"]
        )

        if not self.leaving_request.line_manager_complete:
            return HttpResponseForbidden()

        if not self.line_manager_access(
            request=request,
            leaving_request=self.leaving_request,
        ):
            return HttpResponseForbidden()

        if not self.leaving_request.leaver_complete:
            return HttpResponseNotFound()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()

        context.update(
            page_title="Line manager's off-boarding actions completed",
            leaver_name=leaver_name,
            possessive_leaver_name=make_possessive(leaver_name),
        )
        return context
