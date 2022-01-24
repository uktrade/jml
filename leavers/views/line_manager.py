import os
from typing import Any, Dict

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile  # /PS-IGNORE
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from core.utils.pdf import parse_leaver_pdf
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    StaffDocument,
    consolidate_staff_documents,
    get_staff_document_from_staff_index,
)
from leavers.forms import line_manager as line_manager_forms
from leavers.models import LeavingRequest


class StartView(TemplateView):  # /PS-IGNORE
    template_name = "leaving/line_manager/start.html"

    def dispatch(self, request, *args, **kwargs):
        self.leaving_request = get_object_or_404(
            LeavingRequest, uuid=kwargs["leaving_request_uuid"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            start_url=reverse(
                "line-manager-leaver-confirmation",
                kwargs={"leaving_request_uuid": str(self.leaving_request.uuid)},
            ),
        )
        return context


class LeaverConfirmationView(FormView):
    template_name = "leaving/line_manager/leaver_confirmation.html"
    form_class = line_manager_forms.ConfirmLeavingDate
    # success_url = reverse_lazy("")

    def dispatch(self, request, *args, **kwargs):
        self.leaving_request = get_object_or_404(
            LeavingRequest, uuid=kwargs["leaving_request_uuid"]
        )

        # Load the leaver from the Staff index.
        leaver_staff_document: StaffDocument = get_staff_document_from_staff_index(
            staff_id=self.leaving_request.leaver_activitystream_user.identifier,
        )
        self.leaver: ConsolidatedStaffDocument = consolidate_staff_documents(
            staff_documents=[leaver_staff_document],
        )[0]

        # Load the line manager from the Staff index.
        manager_staff_document: StaffDocument = get_staff_document_from_staff_index(
            staff_id=self.leaving_request.manager_activitystream_user.identifier,
        )
        self.manager: ConsolidatedStaffDocument = consolidate_staff_documents(
            staff_documents=[manager_staff_document],
        )[0]

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        if self.leaving_request.last_day:
            initial["leaving_date"] = self.leaving_request.last_day
        return initial

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        data_recipient = self.manager
        # TODO: Add ability to change the data recipient. And load the stored
        # value here.
        if False:
            data_recipient = {}

        context.update(
            leaver=self.leaver,
            leaver_name=f"{self.leaver['first_name']} {self.leaver['last_name']}",
            data_recipient=data_recipient,
        )
        return context


class DetailsView(FormView):
    template_name = "leaving/line_manager/details.html"
    success_url = reverse_lazy("line-manager-thank-you")
    form_class = line_manager_forms.LineManagerDetailsForm

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        if self.request.POST:
            form_kwargs["files"] = self.request.FILES
        return form_kwargs

    def form_valid(self, form):
        uksbs_pdf: UploadedFile = form.cleaned_data["uksbs_pdf"]
        date_time = timezone.now().strftime("%Y-%m-%d-%H-%M-%S")
        # Store file to disk /PS-IGNORE
        pdf_path = os.path.join(
            settings.MEDIA_ROOT,
            default_storage.save(
                name=f"tmp/{date_time}-{uksbs_pdf.name}",
                content=uksbs_pdf.file,
            ),
        )
        parsed_pdf = parse_leaver_pdf(filename=pdf_path)  # noqa
        # TODO: Store parsed pdf information
        # TODO: Store form details
        return super().form_valid(form)


class ThankYouView(TemplateView):
    template_name = "leaving/line_manager/thank_you.html"
