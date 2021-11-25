from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from core.service_now import get_service_now_interface
from core.service_now import types as service_now_types
from core.utils.people_finder import search_people_finder
from leavers.forms import AddAssetForm, CorrectionForm, LeaverConfirmationForm


class ConfirmDetailsView(FormView):
    form_class = LeaverConfirmationForm
    success_url = reverse_lazy("leaver-request-received")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        people_finder_results = search_people_finder(
            search_term=self.request.user.email,
        )

        context["person"] = people_finder_results[0]

        return context

    template_name = "leaving/leaver/confirm_details.html"


class UpdateDetailsView(FormView):
    template_name = "leaving/leaver/update_details.html"


class KitView(TemplateView):
    asset_form_class = AddAssetForm
    correction_form_class = CorrectionForm
    template_name = "leaving/leaver/kit.html"

    def post(self, request, *args, **kwargs):
        context = {}
        if "asset_name" in request.POST:
            form = self.asset_form_class(request.POST)

            if form.is_valid():
                asset: service_now_types.AssetDetails = {
                    "tag": None,
                    "name": form.cleaned_data["asset_name"],
                }
                request.session["assets"].append(asset)
                request.session.save()
            else:
                context["asset_form"] = form
        else:
            form = self.correction_form_class(request.POST)

            if form.is_valid():
                service_now_interface = get_service_now_interface()
                # TODO: Map form data to the expected format to submit to Service Now.
                leaving_request_data: service_now_types.LeaverRequestData = {
                    "collection_address": {
                        "building_and_street": "",
                        "city": "",
                        "county": "",
                        "postcode": "",
                    },
                    "collection_telephone": "0123456789",
                    "collection_email": "someone@example.com",
                    "reason_for_leaving": "",
                    "leaving_date": timezone.now().date(),
                    "employee_email": "someone@example.com",
                    "employee_name": "Joe Bloggs",
                    "employee_department": "Example Department",
                    "employee_directorate": "Example Directorate",
                    "employee_staff_id": "Staff ID",
                    "manager_name": "Jane Doe",
                    "assets": [],
                    "assets_confirmation": True,
                    "assets_information": "",
                }
                service_now_interface.submit_leaver_request(
                    request_data=leaving_request_data
                )
            else:
                context["correction_form"] = form

        return render(request, self.template_name, self.get_context_data(**context))

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        service_now_interface = get_service_now_interface()
        request.session["assets"] = service_now_interface.get_assets_for_user()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["asset_form"] = self.asset_form_class()
        context["correction_form"] = self.correction_form_class()
        context["assets"] = self.request.session["assets"]

        return context


class RequestReceivedView(TemplateView):
    template_name = "leaving/leaver/request_received.html"
