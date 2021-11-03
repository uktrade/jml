from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.shortcuts import reverse, redirect
from django.views.generic.edit import FormView
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views import View
from django.shortcuts import render

from core.utils.sso import get_sso_user_details
from core.utils.people_finder import search_people_finder

from leavers.models import LeavingRequest

from leavers.forms import (
    PersonNotFoundForm,
    SearchForm,
    WhoIsLeavingForm,
    LeaverConfirmationForm,
)


class LeaversStartView(TemplateView):
    template_name = "leaving/start.html"


class LeavingDetailsView(FormView):
    template_name = "leaving/details.html"
    form_class = WhoIsLeavingForm
    success_url = reverse_lazy("search")

    def form_valid(self, form):
        """If the form is valid, redirect to the supplied URL."""
        self.who_for = form.cleaned_data['who_for']
        return super().form_valid(form)

    def get_success_url(self):
        if self.who_for == "me":
            return reverse("leaver-confirmation")
        else:
            return reverse("search")


class LeavingSearchView(View):
    form_class = SearchForm
    template_name = "leaving/search.html"

    def process_search(self, search_terms):
        emails = []
        names = []

        # Do we split the string and do something smart, do we create an index?
        parts = search_terms.split()

        for part in parts:
            try:
                validate_email(part)
            except ValidationError as e:
                # It's not an email address
                names.append(part)
            else:
                emails.append(part)

        sso_results = []

        # # Do we get anything back from SSO for this email address?
        # for email in emails:
        #     # Search for user in SSO using email
        #     sso_result = get_sso_user_details(
        #         email=email,
        #     )
        #     if sso_result:
        #         sso_results.append(sso_result)

        # Do we get anything back from PF?
        return search_people_finder(
            search_term=search_terms,
        )

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        people_list = []

        if form.is_valid():
            search_terms = form.cleaned_data["search_terms"]
            people_list = self.process_search(
                search_terms,
            )

            # In HR queries use email as key

            # SSO

            # SSO PF

            # SSO PF HR

            # SSO HR

            # PF

            # HR

        return render(request, self.template_name, {
            'form': form,
            'people_list': people_list,
        })


class ConfirmationSummaryView(TemplateView):

    template_name = "leaving/confirmation.html"


class LeaverConfirmationView(FormView):
    template_name = "leaving/leaver-confirmation.html"
    form_class = LeaverConfirmationForm
    success_url = reverse_lazy("leaver-confirmed")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['person'] = {
            "image": "images/ai_person_2.jpg",
            "name": "Sarah Philips",
            "job_title": "Django developer",
            "email": "test@test.com",
            "phone": "07000000000",
        }

        return context


class LeaverConfirmedView(TemplateView):
    template_name = "leaving/leaver-confirmed.html"
