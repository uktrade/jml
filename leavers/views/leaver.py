from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.shortcuts import render
from django.urls import reverse_lazy

from core.utils.people_finder import search_people_finder

from leavers.forms import (
    AddAssetForm,
    CorrectionForm,
    LeaverConfirmationForm,
)


class ConfirmDetailsView(FormView):
    form_class = LeaverConfirmationForm
    success_url = reverse_lazy("leaver-request-received")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        people_finder_results = search_people_finder(
            search_term=self.request.user.email,
        )

        context['person'] = people_finder_results[0]

        return context

    template_name = "leaving/leaver/confirm_details.html"


class UpdateDetailsView(FormView):
    template_name = "leaving/leaver/update_details.html"


class KitView(FormView):
    asset_form_class = AddAssetForm
    correction_form_class = CorrectionForm
    template_name = "leaving/leaver/kit.html"

    def post(self, request, *args, **kwargs):
        context = {}
        if 'asset_name' in request.POST:
            form = self.asset_form_class(request.POST)

            if form.is_valid():
                # Here, save the response
                asset = {
                    "id": 1,
                    "name": form.cleaned_data["asset_name"],
                    "tag": "NOT USED FOR USER INPUT",
                }
                request.session['assets'].append(asset)
                request.session.save()
            else:
                context['asset_form'] = form
        else:
            form = self.correction_form_class(request.POST)

            if form.is_valid():
                pass
            else:
                context['correction_form'] = form

        return render(request, self.template_name, self.get_context_data(**context))

    def get(self, request, *args, **kwargs):
        service_now_assets = [{
            "id": 1,
            "name": "Test asset 1",
            "tag": "Asset tag",
        }, ]
        request.session['assets'] = service_now_assets

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asset_form'] = self.asset_form_class()
        context['correction_form'] = self.correction_form_class()
        context['assets'] = self.request.session['assets']

        return context


class RequestReceivedView(TemplateView):
    template_name = "leaving/leaver/request_received.html"
