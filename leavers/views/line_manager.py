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
from leavers.forms import LineManagerDetailsForm
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
                "line-manager-details",
                kwargs={"leaving_request_uuid": str(self.leaving_request.uuid)},
            ),
        )
        return context


class DetailsView(FormView):
    template_name = "leaving/line_manager/details.html"
    success_url = reverse_lazy("line-manager-thank-you")
    form_class = LineManagerDetailsForm

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
