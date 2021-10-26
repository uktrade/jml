from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from leavers.forms import (
    PersonNotFoundForm,
    SearchForm,
    WhoIsLeavingForm,
)


class LeaversStartView(TemplateView):
    template_name = "leaving/start.html"


class LeavingDetailsView(FormView):
    template_name = "leaving/details.html"
    form_class = WhoIsLeavingForm
    success_url = reverse_lazy("search")

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['who_is_leaving_form'] = self.form_class
    #     return context


class LeavingSearchView(FormView):
    template_name = "leaving/search.html"
    form_class = SearchForm
    success_url = reverse_lazy("search-result")


class LeaverSelectionView(FormView):
    template_name = "leaving/leaver-selection.html"
    form_class = PersonNotFoundForm
    success_url = reverse_lazy("confirmation")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['people_list'] = [
            {
                "image": "images/ai_person_1.jpg",
                "name": "Barry Scott",
                "job_title": "Delivery manager",
                "email": "test@test.com",
                "phone": "07000000000",
            },
            {
                "image": "images/ai_person_2.jpg",
                "name": "Sarah Philips",
                "job_title": "Django developer",
                "email": "test@test.com",
                "phone": "07000000000",
            }
        ]
        return context


class ConfirmationSummaryView(TemplateView):
    template_name = "leaving/confirmation.html"
