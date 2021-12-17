import uuid
from typing import List, Optional, TypedDict

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django_workflow_engine.exceptions import WorkflowNotAuthError
from django_workflow_engine.executor import WorkflowExecutor
from django_workflow_engine.models import Flow

from core.people_finder import get_people_finder_interface
from core.utils.hr import get_hr_people_data
from core.utils.sso import get_sso_user_details
from leavers.forms import LeaverConfirmationForm, SearchForm
from leavers.models import LeavingRequest


class PersonResult(TypedDict):
    uuid: str
    sso_id: str
    email: str
    staff_number: Optional[str]


class LeaverSearchView(View):
    form_class = SearchForm
    template_name = "leaving/line_manager/search.html"
    people_finder_search = get_people_finder_interface()

    # def get_records_from_sso_and_hr_data(self, emails):
    #     sso_results = []
    #     person_results = []
    #
    #     # Do we get anything back from SSO for this email address?
    #     for email in emails:
    #         # Search for user in SSO using email
    #         sso_result = get_sso_user_details(
    #             request=self.request,
    #             email=email,
    #         )
    #         if sso_result:
    #             sso_results.append(sso_result)
    #
    #         for sso_result in sso_results:
    #             hr_data = get_hr_people_data(sso_result["sso_id"])
    #             if hr_data:
    #                 hr_data["uuid"] = str(uuid.uuid4())  # /PS-IGNORE
    #                 hr_data["first_name"] = sso_result["first_name"]  # /PS-IGNORE
    #                 hr_data["last_name"] = sso_result["last_name"]  # /PS-IGNORE
    #                 hr_data["sso_id"] = sso_result["sso_id"]
    #                 person_results.append(  # /PS-IGNORE
    #                     hr_data,
    #                 )  # /PS-IGNORE
    #
    #     return person_results

    def get_pf_results_with_sso_id(self, search_terms):
        people_finder_results = self.people_finder_search.get_search_results(
            search_term=search_terms,
        )

        # Look for SSO id
        results_found_in_sso = []

        for pf_result in people_finder_results:
            # TODO make SSO logic return user for ANY of their
            # TODO email addresses
            # TODO use all email addresses associated with PF result
            sso_result = get_sso_user_details(
                request=self.request,
                email=pf_result["email"],
            )

            if sso_result:
                pf_result["sso_id"] = sso_result["sso_id"]
                pf_result["uuid"] = str(uuid.uuid4())

                # Add relevant HR data
                hr_data = get_hr_people_data(sso_result["sso_id"])
                if hr_data:
                    pf_result["staff_number"] = hr_data["staff_number"]

                results_found_in_sso.append(
                    pf_result,
                )

        return results_found_in_sso

    def process_search(self, search_terms):
        emails: List[str] = []

        # Create list of emails used in search query
        for part in search_terms.split():
            try:
                validate_email(part)
            except ValidationError as e:
                print(e)
                # It's not an email address
                pass
            else:
                emails.append(part)

        person_results: List[PersonResult] = []

        for email in emails:
            sso_result = get_sso_user_details(request=self.request, email=email)
            if sso_result:
                person_results.append(
                    {
                        "uuid": str(uuid.uuid4()),
                        "sso_id": sso_result["sso_id"],
                        "email": email,
                        "staff_number": None,
                    }
                )

        # We do not present a result unless
        # we have been able to establish SSO id
        # Results are either from PF
        # or constructed from SSO and HR data

        person_results = self.get_pf_results_with_sso_id(
            search_terms,
        )

        # Do we get anything back from PF?
        if len(person_results) == 0:
            # We need to construct results from SSO id and HR data
            person_results = self.get_records_from_sso_and_hr_data(
                emails=emails,
            )

        return person_results

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        people_list = []

        if form.is_valid():
            search_terms = form.cleaned_data["search_terms"]
            people_list = self.process_search(
                search_terms,
            )

            request.session["people_list"] = people_list

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "people_list": people_list,
            },
        )


class ConfirmationView(FormView):
    template_name = "leaving/line_manager/confirm.html"
    form_class = LeaverConfirmationForm
    success_url = reverse_lazy("report-a-leaver-request-received")

    def dispatch(self, request, *args, **kwargs):
        # UUID created when we created people list
        person_id = request.GET.get("person_id", None)
        if not person_id:
            redirect("report-a-leaver-search")

        for person in self.request.session["people_list"]:
            if person["uuid"] == person_id:
                self.person = person

        return super().dispatch(request, *args, **kwargs)

    def create_workflow(self):
        flow = Flow.objects.create(
            workflow_name="leaving",
            flow_name=f"{self.person['first_name']} {self.person['last_name']} is leaving",  # noqa E501
            executed_by=self.request.user,
        )
        flow.save()

        LeavingRequest.objects.create(
            leaver_sso_id=self.person["sso_id"],
            user_requesting=self.request.user,
            flow=flow,
            leaver_first_name=self.person["first_name"],
            leaver_last_name=self.person["last_name"],
        )

        executor = WorkflowExecutor(flow)

        try:
            executor.run_flow(user=self.request.user)
        except WorkflowNotAuthError as e:
            raise PermissionDenied(f"{e}")

    def form_valid(self, form):
        # Need to find out SSO id here
        self.create_workflow()

        # Need to validate user is correct record here
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["person"] = self.person

        return context


class RequestReceivedView(TemplateView):
    template_name = "leaving/line_manager/request_received.html"
