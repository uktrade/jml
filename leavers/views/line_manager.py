import os
from typing import Any, Dict

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile  # /PS-IGNORE
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from core.utils.pdf import parse_leaver_pdf
from leavers.forms import LineManagerDetailsForm


class ProcessInformationView(TemplateView):  # /PS-IGNORE
    template_name = "leaving/line_manager_return/process_information.html"


class DetailsView(FormView):
    template_name = "leaving/line_manager_return/details.html"
    success_url = reverse_lazy("line-manager-return-thank-you")
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
    template_name = "leaving/line_manager_return/thank_you.html"
