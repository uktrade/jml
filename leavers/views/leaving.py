from django.shortcuts import redirect, reverse
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from leavers.forms import (
    LeaverConfirmationForm,
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

    def form_valid(self, form):
        """If the form is valid, redirect to the supplied URL."""
        self.who_for = form.cleaned_data["who_for"]
        return super().form_valid(form)

    def get_success_url(self):
        if self.who_for == "me":
            return reverse("leaver-confirmation")
        else:
            return reverse("search")


class LeavingSearchView(FormView):
    template_name = "leaving/search.html"
    form_class = SearchForm
    success_url = reverse_lazy("leaver-selection")


class LeaverSelectionView(FormView):
    template_name = "leaving/leaver-selection.html"
    form_class = PersonNotFoundForm
    success_url = reverse_lazy("confirmation")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["people_list"] = [
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
            },
        ]
        return context


class ConfirmationSummaryView(TemplateView):
    template_name = "leaving/confirmation.html"


class LeaverConfirmationView(FormView):
    template_name = "leaving/leaver-confirmation.html"
    form_class = LeaverConfirmationForm
    success_url = reverse_lazy("leaver-confirmed")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["person"] = {
            "image": "images/ai_person_2.jpg",
            "name": "Sarah Philips",
            "job_title": "Django developer",
            "email": "test@test.com",
            "phone": "07000000000",
        }

        return context


class LeaverConfirmedView(TemplateView):
    template_name = "leaving/leaver-confirmed.html"
