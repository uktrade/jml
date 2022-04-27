import os
from typing import Any, Dict, Optional, cast

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from activity_stream.models import ActivityStreamStaffSSOUser
from core.staff_search.views import StaffSearchView
from core.utils.helpers import bool_to_yes_no
from core.utils.pdf import parse_leaver_pdf
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    StaffDocument,
    consolidate_staff_documents,
    get_staff_document_from_staff_index,
)
from leavers.forms import line_manager as line_manager_forms
from leavers.models import LeaverInformation, LeavingRequest
from user.models import User

DATA_RECIPIENT_SEARCH_PARAM = "data_recipient_id"


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
        if user.email != manager_activitystream_user.email_address:
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

        context.update(
            page_title="Confirmation of leavers details",
            start_url=reverse(
                "line-manager-leaver-confirmation",
                kwargs={"leaving_request_uuid": str(self.leaving_request.uuid)},
            ),
            leaver_name=self.leaving_request.get_leaver_name(),
        )

        return context


class LeaverConfirmationView(LineManagerViewMixin, FormView):
    template_name = "leaving/line_manager/leaver_confirmation.html"
    form_class = line_manager_forms.ConfirmLeavingDate

    def get_success_url(self) -> str:
        return reverse(
            "line-manager-uksbs-handover",
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )

    def get_leaver(self) -> ConsolidatedStaffDocument:
        """
        Get the Leaver StaffDocument
        """
        # Load the leaver from the Staff index.
        leaver_staff_document: StaffDocument = get_staff_document_from_staff_index(
            staff_id=self.leaving_request.leaver_activitystream_user.identifier,
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
            staff_id=self.leaving_request.manager_activitystream_user.identifier,
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
                staff_id=self.leaving_request.data_recipient_activitystream_user.identifier
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
        return initial

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(
            page_title="Title of page",
            leaver=self.leaver,
            leaver_name=f"{self.leaver['first_name']} {self.leaver['last_name']}",
            data_recipient=self.data_recipient or self.manager,
            data_recipient_search=reverse(
                "line-manager-data-recipient-search",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
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
        self.leaving_request.save()

        return super().form_valid(form)


class UksbsHandoverView(LineManagerViewMixin, FormView):
    template_name = "leaving/line_manager/uksbs-handover.html"
    form_class = line_manager_forms.UksbsPdfForm

    def get_success_url(self) -> str:
        return reverse(
            "line-manager-details",
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )

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

        if self.leaving_request.uksbs_pdf_data:
            # TODO: Discuss, the assumption here is that if the data is already in the
            # LeavingRequest, we will just redirect users to the details step.
            # Perhaps this isn't the intended behaviour, instead we might want to show
            # a message to inform the user that they have already uploaded the form.
            return redirect(self.get_success_url())

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        if self.request.POST:
            form_kwargs["files"] = self.request.FILES
        return form_kwargs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(page_title="UKSBS handover")

        # TODO: Remove Staff Index search from this view.
        # Load the leaver from the Staff index.
        leaver_staff_document: StaffDocument = get_staff_document_from_staff_index(
            staff_id=self.leaving_request.leaver_activitystream_user.identifier,
        )
        leaver: ConsolidatedStaffDocument = consolidate_staff_documents(
            staff_documents=[leaver_staff_document],
        )[0]

        leaver_information: LeaverInformation = (
            self.leaving_request.leaver_information.first()
        )
        if not leaver_information:
            raise Exception("Unable to find leaver information.")

        # Update context with leaver information.
        context.update(
            leaver_name=f"{leaver['first_name']} {leaver['last_name']}",
            leaver_email=leaver_information.leaver_email,
            leaver_address=leaver_information.display_address,
            leaver_phone=leaver_information.return_personal_phone,
        )
        return context

    def form_valid(self, form):
        uksbs_pdf: UploadedFile = form.cleaned_data["uksbs_pdf"]
        date_time = timezone.now().strftime("%Y-%m-%d-%H-%M-%S")

        # Store file to disk
        pdf_path = os.path.join(
            settings.MEDIA_ROOT,
            default_storage.save(
                name=f"tmp/{date_time}-{uksbs_pdf.name}",
                content=uksbs_pdf.file,
            ),
        )

        # Store parsed data against the LeavingRequest.
        parsed_pdf = parse_leaver_pdf(filename=pdf_path)
        self.leaving_request.uksbs_pdf_data = parsed_pdf
        self.leaving_request.save()

        return super().form_valid(form)


class DetailsView(LineManagerViewMixin, FormView):
    template_name = "leaving/line_manager/details.html"
    form_class = line_manager_forms.LineManagerDetailsForm

    def get_success_url(self) -> str:
        return reverse(
            "line-manager-confirmation",
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        if self.leaving_request:
            # Security Clearance
            if self.leaving_request.security_clearance:
                initial["security_clearance"] = self.leaving_request.security_clearance
            # ROSA user
            is_rosa_user = self.leaving_request.is_rosa_user
            if is_rosa_user is not None:
                rosa_user_yes_no = bool_to_yes_no(is_rosa_user)
                initial["rosa_user"] = rosa_user_yes_no
            # Government Procurement Card
            holds_government_procurement_card = (
                self.leaving_request.holds_government_procurement_card
            )
            if holds_government_procurement_card is not None:
                holds_government_procurement_card_yes_no = (
                    "yes" if holds_government_procurement_card else "no"
                )
                initial[
                    "holds_government_procurement_card"
                ] = holds_government_procurement_card_yes_no
        return initial

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

    def form_valid(self, form) -> HttpResponse:
        # Store the details against the LeavingRequest.
        self.leaving_request.security_clearance = form.cleaned_data[
            "security_clearance"
        ]
        self.leaving_request.is_rosa_user = bool(
            form.cleaned_data["rosa_user"] == "yes"
        )
        self.leaving_request.holds_government_procurement_card = bool(
            form.cleaned_data["holds_government_procurement_card"] == "yes"
        )
        self.leaving_request.save()

        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(
            page_title="Confirm the Leaver's information",
            leaver_name=self.leaving_request.get_leaver_name(),
        )

        return context


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
            staff_id=self.leaving_request.leaver_activitystream_user.identifier,
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
            staff_id=self.leaving_request.data_recipient_activitystream_user.identifier,
        )
        return consolidate_staff_documents(
            staff_documents=[data_recipient_staff_document],
        )[0]

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

        self.leaver: ConsolidatedStaffDocument = self.get_leaver()
        self.data_recipient: ConsolidatedStaffDocument = self.get_data_recipient()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(
            page_title="Confirm all the information",
            leaver_name=self.leaving_request.get_leaver_name(),
            leaver=self.leaver,
            data_recipient=self.data_recipient,
            last_day=self.leaving_request.last_day.date(),
            leaving_date=self.leaving_request.leaving_date.date(),
            uksbs_pdf_data=self.leaving_request.uksbs_pdf_data,
            has_security_clearance=self.leaving_request.get_security_clearance_display(),
            is_rosa_user=bool_to_yes_no(self.leaving_request.is_rosa_user).title(),
            holds_government_procurement_card=bool_to_yes_no(
                self.leaving_request.holds_government_procurement_card
            ).title(),
            leaver_confirmation_view_url=reverse_lazy(
                "line-manager-leaver-confirmation",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
            details_view_url=reverse_lazy(
                "line-manager-details",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
            uksbs_upload_view_url=reverse_lazy(
                "line-manager-uksbs-handover",
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
        context.update(
            page_title="Application complete",
            leaver_name=self.leaving_request.get_leaver_name(),
        )
        return context
