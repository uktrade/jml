from datetime import date
from typing import Any, Dict, List, Optional, cast
from uuid import UUID, uuid4

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseRedirect,
)
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import resolve, reverse
from django.utils import timezone
from django.views.generic import RedirectView
from django.views.generic.edit import FormView

from activity_stream.models import ActivityStreamStaffSSOUser
from core.staff_search.views import StaffSearchView
from core.uksbs import get_uksbs_interface
from core.uksbs.client import UKSBSPersonNotFound, UKSBSUnexpectedResponse
from core.uksbs.types import PersonData, PersonHierarchyData
from core.utils.helpers import make_possessive
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    StaffDocument,
    StaffDocumentNotFound,
    TooManyStaffDocumentsFound,
    consolidate_staff_documents,
    get_staff_document_from_staff_index,
)
from core.views import BaseTemplateView
from leavers.exceptions import LeaverDoesNotHaveUKSBSPersonId
from leavers.forms import line_manager as line_manager_forms
from leavers.models import LeavingRequest
from leavers.types import LeavingReason, LeavingRequestLineReport
from leavers.views.leaver import LeavingRequestViewMixin
from user.models import User

DATA_RECIPIENT_SEARCH_PARAM = "data_recipient_id"
LINE_REPORT_NEW_LINE_MANAGER_SEARCH_PARAM = "new_line_manager_id"
LINE_REPORT_SET_NEW_MANAGER_ERROR = "line_report_set_new_manager_error"
ADD_MISSING_LINE_REPORT_ERROR = "add_missing_line_report_error"


class LineManagerViewMixin:
    user_is_line_manager: bool = False

    def get_page_count(
        self,
        leaving_request: LeavingRequest,
    ) -> int:
        page_count = 2
        if leaving_request.show_hr_and_payroll:
            page_count += 1
        if leaving_request.show_line_reports:
            page_count += 1
        return page_count

    def user_is_manager(
        self,
        request: HttpRequest,
        leaving_request: LeavingRequest,
    ) -> bool:
        user = cast(User, request.user)

        manager_activitystream_user: Optional[
            ActivityStreamStaffSSOUser
        ] = leaving_request.manager_activitystream_user

        # If we don't know the manager, no one can access this view.
        if not manager_activitystream_user:
            return False

        # If the user is the manager that the leaver selected, they can access the view.
        if user.sso_email_user_id == manager_activitystream_user.email_user_id:
            self.user_is_line_manager = True
            return True
        return False

    def user_is_uksbs_manager(
        self,
        request: HttpRequest,
        leaving_request: LeavingRequest,
    ) -> bool:
        user = cast(User, request.user)
        # If the user is the manager that the leaver is currently assigned to in UK SBS,
        # they can access the view.
        try:
            user_activitystream_user: ActivityStreamStaffSSOUser = (
                ActivityStreamStaffSSOUser.objects.active().get(
                    email_user_id=user.sso_email_user_id,
                )
            )
        except ActivityStreamStaffSSOUser.DoesNotExist:
            return False

        user_person_id = user_activitystream_user.get_person_id()
        leaver_person_id = None
        if leaving_request.leaver_activitystream_user:
            leaver_person_id = (
                leaving_request.leaver_activitystream_user.get_person_id()
            )

        if (
            not leaving_request.leaver_activitystream_user
            or not leaver_person_id
            or not user_person_id
        ):
            return False

        uksbs_interface = get_uksbs_interface()

        try:
            leaver_hierarchy_data = uksbs_interface.get_user_hierarchy(
                person_id=leaver_person_id
            )
        except (UKSBSUnexpectedResponse, UKSBSPersonNotFound):
            return False

        for uksbs_manager in leaver_hierarchy_data.get("manager", []):
            if str(uksbs_manager["person_id"]) == str(user_person_id):
                # The user is in UK SBS as the manager of the leaver.
                leaving_request.processing_manager_activitystream_user = (
                    user_activitystream_user
                )
                leaving_request.save(
                    update_fields=["processing_manager_activitystream_user"]
                )
                self.user_is_line_manager = True
                return True
        return False

    def line_manager_access(
        self,
        request: HttpRequest,
        leaving_request: LeavingRequest,
    ) -> bool:
        """
        Check to see if the user that is trying to process the Leaving Request is
        actually a manager of the leaver.
        - The manager that the Leaver selected
        - The manager that the Leaver is currently assigned to in UK SBS

        Sets the leaving_reqeust.processing_manager_activitystream_user accordingly.
        """

        user = cast(User, request.user)
        leaver_activitystream_user: Optional[
            ActivityStreamStaffSSOUser
        ] = leaving_request.leaver_activitystream_user

        # If we don't know the Leaver, no one can access this view.
        if not leaver_activitystream_user:
            return False

        user_activitystream_user = user.get_sso_user()

        if leaver_activitystream_user == user_activitystream_user:
            return False

        # If the user is the processing manager, they can access the view.
        processing_manager_activitystream_user: Optional[
            ActivityStreamStaffSSOUser
        ] = leaving_request.processing_manager_activitystream_user
        if (
            processing_manager_activitystream_user
            and user.sso_email_user_id
            == processing_manager_activitystream_user.email_user_id
        ):
            return True

        if self.user_is_manager(request=request, leaving_request=leaving_request):
            return True

        if self.user_is_uksbs_manager(request=request, leaving_request=leaving_request):
            return True

        if user.has_perm("leavers.select_leaver"):
            return True

        return False


class IsReviewUser(UserPassesTestMixin):
    # TODO: Switch to a permission check
    def test_func(self):
        return self.line_manager_access(
            request=self.request,
            leaving_request=self.leaving_request,
        )


class ReviewViewMixin(IsReviewUser, LineManagerViewMixin, LeavingRequestViewMixin):
    def pre_dispatch(self, request, *args, **kwargs) -> Optional[HttpResponse]:
        return None

    def dispatch(self, request, *args, **kwargs):
        if not self.leaving_request.leaver_complete:
            return HttpResponseNotFound()

        self.user_is_manager

        if (
            self.leaving_request.line_manager_complete
            and resolve(self.request.path).view_name != "line-manager-thank-you"
        ):
            return redirect(self.get_view_url("line-manager-thank-you"))

        if response := self.pre_dispatch(request, *args, **kwargs):
            return response

        user = cast(User, request.user)

        # Make sure the current user is set as the processing manager
        user_sso_user = user.get_sso_user()
        if (
            self.leaving_request.processing_manager_activitystream_user != user_sso_user
            and resolve(self.request.path).view_name != "line-manager-start"
        ):
            self.leaving_request.processing_manager_activitystream_user = user_sso_user
            self.leaving_request.save(
                update_fields=["processing_manager_activitystream_user"]
            )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(user_is_line_manager=self.user_is_line_manager)
        return context


class DataRecipientSearchView(ReviewViewMixin, StaffSearchView):
    search_name = "data recipient"
    query_param_name = DATA_RECIPIENT_SEARCH_PARAM
    success_viewname = "line-manager-leaver-confirmation"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.exclude_staff_ids = [
            self.leaving_request.leaver_activitystream_user.identifier
        ]


class LineReportNewLineManagerSearchView(ReviewViewMixin, StaffSearchView):
    search_name = "new Line Manager"
    query_param_name = LINE_REPORT_NEW_LINE_MANAGER_SEARCH_PARAM

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.exclude_staff_ids = [
            self.leaving_request.leaver_activitystream_user.identifier
        ]

    def get_success_url(self) -> str:
        return self.get_view_url(
            "line-reports-set-new-manager",
            line_report_uuid=self.request.GET["line_report_uuid"],
        )


class StartView(ReviewViewMixin, BaseTemplateView):
    template_name = "leaving/line_manager/start.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()

        title_reason = "leaving"
        if self.leaving_request.reason_for_leaving == LeavingReason.TRANSFER.value:
            title_reason = "transfering to another Government department"
        page_title = f"{leaver_name} is {title_reason}: what you need to do"

        context.update(
            page_title=page_title,
            start_url=self.get_view_url("line-manager-leaver-confirmation"),
            leaver_name=leaver_name,
            possessive_leaver_name=make_possessive(leaver_name),
            reason_for_leaving=self.leaving_request.reason_for_leaving,
        )

        return context


class RemoveDataRecipientFromLeavingRequestView(ReviewViewMixin, RedirectView):
    def get_redirect_url(self, *args: Any, **kwargs: Any) -> Optional[str]:
        return self.get_view_url("line-manager-leaver-confirmation")

    def get(self, request, *args, **kwargs):
        self.leaving_request.data_recipient_activitystream_user = None
        self.leaving_request.save(update_fields=["data_recipient_activitystream_user"])

        return super().get(request, *args, **kwargs)


class LeaverConfirmationView(ReviewViewMixin, BaseTemplateView, FormView):
    template_name = "leaving/line_manager/leaver_confirmation.html"
    form_class = line_manager_forms.ConfirmLeavingDate
    success_viewname = "line-manager-details"
    back_link_viewname = "line-manager-start"

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(
            request=self.request,
            leaving_request_uuid=self.leaving_request.uuid,
            leaver=self.get_leaver(),
            needs_data_transfer=self.leaver_has_digital_email,
        )
        return form_kwargs

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
        manager_as_user = self.leaving_request.get_line_manager()
        assert manager_as_user
        # Load the Line Manager from the Staff index.
        manager_staff_document: StaffDocument = get_staff_document_from_staff_index(
            sso_email_user_id=manager_as_user.email_user_id,
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
                    ActivityStreamStaffSSOUser.objects.active().get(
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

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.leaver: ConsolidatedStaffDocument = self.get_leaver()
        self.manager: ConsolidatedStaffDocument = self.get_manager()

        self.leaver_has_digital_email: bool = (
            self.leaving_request.leaver_activitystream_user.sso_emails.filter(
                email_address__contains="@digital.trade.gov.uk",
            ).exists()
        )

        self.data_recipient: Optional[ConsolidatedStaffDocument] = None

        if self.leaver_has_digital_email:
            self.data_recipient_activitystream_user: Optional[
                ActivityStreamStaffSSOUser
            ] = None
            self.get_data_recipient(request)

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()

        initial["leaving_date"] = self.leaving_request.get_leaving_date()
        initial["last_day"] = self.leaving_request.get_last_day()

        if self.data_recipient:
            initial.update(
                data_recipient=self.data_recipient["uuid"],
            )

        return initial

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:

        context = super().get_context_data(**kwargs)

        leaver_name = f"{self.leaver['first_name']} {self.leaver['last_name']}"
        possessive_leaver_name = make_possessive(leaver_name)

        context.update(
            page_title=f"Confirm {possessive_leaver_name} information",
            page_count=self.get_page_count(leaving_request=self.leaving_request),
            leaver=self.leaver,
            leaver_name=leaver_name,
            possessive_leaver_name=possessive_leaver_name,
            data_recipient=self.data_recipient or self.manager,
            data_recipient_search=self.get_view_url(
                "line-manager-data-recipient-search"
            ),
        )
        return context

    def form_valid(self, form) -> HttpResponse:
        if self.leaver_has_digital_email:
            # If there is no data recipient set, we set the recipient as the manager.
            if not self.data_recipient:
                self.leaving_request.data_recipient_activitystream_user = (
                    self.leaving_request.manager_activitystream_user
                )
        else:
            # Set the value to none if the leaver doesn't have a digital email.
            self.leaving_request.data_recipient_activitystream_user = None

        # Store the leaving date against the LeavingRequest.
        self.leaving_request.last_day = form.cleaned_data["last_day"]
        self.leaving_request.leaving_date = form.cleaned_data["leaving_date"]
        self.leaving_request.save()

        return super().form_valid(form)


class DetailsView(ReviewViewMixin, BaseTemplateView, FormView):
    template_name = "leaving/line_manager/details.html"
    form_class = line_manager_forms.LineManagerDetailsForm
    success_viewname = "line-manager-leaver-line-reports"
    back_link_viewname = "line-manager-leaver-confirmation"

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

    def pre_dispatch(self, request, *args, **kwargs):
        if not self.leaving_request.show_hr_and_payroll:
            return redirect(self.get_success_url())

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

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(
            page_title="HR and payroll",
            page_count=self.get_page_count(leaving_request=self.leaving_request),
            leaver_name=self.leaving_request.get_leaver_name(),
            leaver=self.get_leaver(),
        )

        return context


# TODO: Refactor to use the ReviewBaseView
def line_report_set_new_manager(
    request: HttpRequest, leaving_request_uuid: UUID, line_report_uuid: UUID
) -> HttpResponse:
    leaving_request = get_object_or_404(LeavingRequest, uuid=leaving_request_uuid)

    if not leaving_request.leaver_complete:
        return HttpResponseNotFound()

    if leaving_request.line_manager_complete:
        return redirect(
            reverse(
                "line-manager-thank-you",
                kwargs={"leaving_request_uuid": leaving_request_uuid},
            )
        )

    redirect_response = HttpResponseRedirect(
        reverse(
            "line-manager-leaver-line-reports",
            kwargs={"leaving_request_uuid": leaving_request_uuid},
        )
    )

    lr_line_reports: List[LeavingRequestLineReport] = leaving_request.line_reports

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
        line_manager_uuid = consolidated_staff_document["uuid"]
        line_manager_name = (
            consolidated_staff_document["first_name"]
            + " "
            + consolidated_staff_document["last_name"]
        )
        try:
            line_manager_as_user: ActivityStreamStaffSSOUser = (
                ActivityStreamStaffSSOUser.objects.active().get(
                    email_user_id=consolidated_staff_document[
                        "staff_sso_email_user_id"
                    ],
                )
            )
        except ActivityStreamStaffSSOUser.DoesNotExist:
            request.session[
                LINE_REPORT_SET_NEW_MANAGER_ERROR
            ] = f"Unable to add {line_manager_name} as a Line Manager, please try again later."
            return redirect_response

        try:
            line_manager_email = line_manager_as_user.get_email_addresses_for_contact()[
                0
            ]
        except Exception:
            request.session[
                LINE_REPORT_SET_NEW_MANAGER_ERROR
            ] = f"Unable to add {line_manager_name} as a Line Manager, please try again later."
            return redirect_response

        for line_report in lr_line_reports:
            if line_report["uuid"] == str(line_report_uuid):
                line_report["line_manager"] = {
                    "staff_uuid": line_manager_uuid,
                    "name": line_manager_name,
                    "email": line_manager_email,
                }
                break

        leaving_request.line_reports = lr_line_reports
        leaving_request.save()

    return redirect_response


class RemoveLineManagerFromLineReportView(ReviewViewMixin, RedirectView):
    def get_redirect_url(self, *args: Any, **kwargs: Any) -> Optional[str]:
        return self.get_view_url("line-manager-leaver-line-reports")

    def pre_dispatch(self, request, *args, **kwargs):
        self.line_report_uuid = self.request.GET.get("line_report_uuid")

        if not self.line_report_uuid:
            return HttpResponseBadRequest()

    def get(self, request, *args, **kwargs):
        lr_line_reports: List[
            LeavingRequestLineReport
        ] = self.leaving_request.line_reports
        for line_report in lr_line_reports:
            if line_report["uuid"] == str(self.line_report_uuid):
                line_report["line_manager"] = None
                break

        self.leaving_request.line_reports = lr_line_reports
        self.leaving_request.save(update_fields=["line_reports"])

        return super().get(request, *args, **kwargs)


class LeaverLineReportsView(ReviewViewMixin, BaseTemplateView, FormView):
    template_name = "leaving/line_manager/line_reports.html"
    form_class = line_manager_forms.LineReportConfirmationForm
    success_viewname = "line-manager-confirmation"
    back_link_viewname = "line-manager-details"

    def initialize_line_reports(self) -> None:
        if not self.leaving_request.line_reports:
            uksbs_interface = get_uksbs_interface()
            leaver_as_user: ActivityStreamStaffSSOUser = (
                self.leaving_request.leaver_activitystream_user
            )
            leaver_person_id = leaver_as_user.get_person_id()
            if not leaver_person_id:
                raise LeaverDoesNotHaveUKSBSPersonId()

            leaver_hierarchy_data: PersonHierarchyData = (
                uksbs_interface.get_user_hierarchy(
                    person_id=leaver_person_id,
                )
            )
            person_data_line_reports: List[PersonData] = leaver_hierarchy_data.get(
                "report", []
            )

            lr_line_reports: List[LeavingRequestLineReport] = []
            for line_report in person_data_line_reports:
                consolidated_staff_document: Optional[ConsolidatedStaffDocument] = None
                try:
                    staff_document = get_staff_document_from_staff_index(
                        sso_email_address=line_report["email_address"]
                    )
                    consolidated_staff_document = consolidate_staff_documents(
                        staff_documents=[staff_document]
                    )[0]
                except (StaffDocumentNotFound, TooManyStaffDocumentsFound):
                    pass
                lr_line_reports.append(
                    {
                        "uuid": str(uuid4()),
                        "name": line_report["full_name"],
                        "email": line_report["email_address"],
                        "line_manager": None,
                        "person_data": line_report,
                        "consolidated_staff_document": consolidated_staff_document,
                    }
                )

            self.leaving_request.line_reports = lr_line_reports
            self.leaving_request.save()

    def pre_dispatch(self, request, *args, **kwargs):
        self.initialize_line_reports()

        if not self.leaving_request.line_reports:
            return redirect(self.get_success_url())

        if not self.leaving_request.show_line_reports:
            return redirect(self.get_success_url())

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

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        errors: List[str] = []
        line_report_set_new_manager_error: Optional[str] = self.request.session.get(
            LINE_REPORT_SET_NEW_MANAGER_ERROR
        )
        if line_report_set_new_manager_error:
            errors.append(line_report_set_new_manager_error)
            self.request.session[LINE_REPORT_SET_NEW_MANAGER_ERROR] = None
        add_missing_line_report_error: Optional[str] = self.request.session.get(
            ADD_MISSING_LINE_REPORT_ERROR
        )
        if add_missing_line_report_error:
            errors.append(add_missing_line_report_error)
            self.request.session[ADD_MISSING_LINE_REPORT_ERROR] = None

        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name = make_possessive(leaver_name)

        context.update(
            page_title=f"{possessive_leaver_name} line reports",
            page_count=self.get_page_count(leaving_request=self.leaving_request),
            leaver_name=leaver_name,
            line_reports=self.leaving_request.line_reports,
            leaver=self.get_leaver(),
            new_line_manager_search=self.get_view_url(
                "line-manager-line-report-new-line-manager-search",
            ),
            remove_new_line_manager=self.get_view_url(
                "remove-line-manager-from-line-report",
            ),
            errors=errors,
        )

        return context

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs["leaving_request"] = self.leaving_request
        return form_kwargs


class ConfirmDetailsView(ReviewViewMixin, BaseTemplateView, FormView):
    template_name = "leaving/line_manager/confirm_details.html"
    form_class = line_manager_forms.LineManagerConfirmationForm
    success_viewname = "line-manager-thank-you"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.leaver = self.get_leaver()
        self.data_recipient = self.get_data_recipient()

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

    def get_data_recipient(self) -> Optional[ConsolidatedStaffDocument]:
        """
        Get the Data Recipient StaffDocument
        """
        if not self.leaving_request.data_recipient_activitystream_user:
            return None

        # Load the Data Recipient from the Staff index.
        data_recipient_staff_document: StaffDocument = get_staff_document_from_staff_index(
            sso_email_user_id=self.leaving_request.data_recipient_activitystream_user.email_user_id,
        )
        return consolidate_staff_documents(
            staff_documents=[data_recipient_staff_document],
        )[0]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name = make_possessive(leaver_name)

        annual_leave: Optional[str] = None
        has_annual_leave: Optional[bool] = None
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
        has_flexi_leave: Optional[bool] = None
        if self.leaving_request.flexi_leave:
            flexi_leave_enum = line_manager_forms.FlexiLeavePaidOrDeducted(
                self.leaving_request.flexi_leave
            )
            flexi_leave = flexi_leave_enum.label
            has_flexi_leave = bool(flexi_leave_enum.value != "None")

        leaving_datetime = self.leaving_request.get_leaving_date()
        leaving_date: Optional[date] = None
        if leaving_datetime:
            leaving_date = leaving_datetime.date()

        last_day_datetime = self.leaving_request.get_last_day()
        last_day: Optional[date] = None
        if last_day_datetime:
            last_day = last_day_datetime.date()

        context.update(
            page_title="Check and confirm your answers",
            page_count=self.get_page_count(leaving_request=self.leaving_request),
            leaver_name=leaver_name,
            possessive_leaver_name=possessive_leaver_name,
            leaver=self.leaver,
            data_recipient=self.data_recipient,
            leaving_date=leaving_date,
            last_day=last_day,
            annual_leave=annual_leave,
            has_annual_leave=has_annual_leave,
            annual_leave_measurement=annual_leave_measurement,
            annual_number=self.leaving_request.annual_number,
            flexi_leave=flexi_leave,
            has_flexi_leave=has_flexi_leave,
            flexi_number=self.leaving_request.flexi_number,
            line_reports=self.leaving_request.line_reports,
            leaver_confirmation_view_url=self.get_view_url(
                "line-manager-leaver-confirmation",
            ),
            details_view_url=self.get_view_url(
                "line-manager-details",
            ),
            line_reports_view=self.get_view_url(
                "line-manager-leaver-line-reports",
            ),
        )

        return context

    def form_valid(self, form) -> HttpResponse:
        self.leaving_request.line_manager_complete = timezone.now()
        self.leaving_request.save()

        return super().form_valid(form)

    def get_back_link_url(self):
        back_url = self.get_view_url("line-manager-leaver-confirmation")

        if self.leaving_request.show_line_reports:
            back_url = self.get_view_url("line-manager-leaver-line-reports")
        elif self.leaving_request.show_hr_and_payroll:
            back_url = self.get_view_url("line-manager-details")

        return back_url


class ThankYouView(ReviewViewMixin, BaseTemplateView):
    template_name = "leaving/line_manager/thank_you.html"

    def pre_dispatch(self, request, *args, **kwargs):
        if not self.leaving_request.line_manager_complete:
            return HttpResponseForbidden()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()

        context.update(
            page_title="Leaving form completed",
            leaver_name=leaver_name,
            leaving_request=self.leaving_request,
            leaver_information=self.leaver_info,
            cirrus_assets=self.leaver_info.cirrus_assets,
            possessive_leaver_name=make_possessive(leaver_name),
        )
        return context


class OfflineServiceNowBaseView(
    IsReviewUser, LineManagerViewMixin, LeavingRequestViewMixin
):
    def dispatch(self, request, *args, **kwargs):
        if not self.leaving_request.leaver_complete:
            return HttpResponseNotFound()

        if not self.leaving_request.service_now_offline:
            return HttpResponseNotFound()

        if not self.leaving_request.line_manager_complete:
            return HttpResponseForbidden()

        return super().dispatch(request, *args, **kwargs)


class OfflineServiceNowView(OfflineServiceNowBaseView, BaseTemplateView, FormView):
    template_name = "leaving/line_manager/offline_service_now.html"
    form_class = line_manager_forms.OfflineServiceNowForm
    success_viewname = "line-manager-offline-service-now-thank-you"

    def dispatch(self, request, *args, **kwargs):
        if self.leaving_request.line_manager_service_now_complete:
            return redirect(self.get_success_url())

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()

        context.update(
            page_title="Log a Service Now request",
            leaver_name=leaver_name,
            leaving_request=self.leaving_request,
            leaver_information=self.leaver_info,
            cirrus_assets=self.leaver_info.cirrus_assets,
            possessive_leaver_name=make_possessive(leaver_name),
        )
        return context

    def form_valid(self, form) -> HttpResponse:
        self.leaving_request.line_manager_service_now_complete = timezone.now()
        self.leaving_request.save(update_fields=["line_manager_service_now_complete"])

        return super().form_valid(form)


class OfflineServiceNowThankYouView(OfflineServiceNowBaseView, BaseTemplateView):
    template_name = "leaving/line_manager/offline_service_now_thank_you.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()

        context.update(
            page_title="Thank you",
            leaver_name=leaver_name,
            possessive_leaver_name=make_possessive(leaver_name),
        )
        return context
