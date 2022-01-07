from typing import List

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django_workflow_engine.exceptions import WorkflowNotAuthError
from django_workflow_engine.executor import WorkflowExecutor
from django_workflow_engine.models import Flow

from activity_stream.models import ActivityStreamStaffSSOUser
from core.people_finder import get_people_finder_interface
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    consolidate_staff_documents,
    search_staff_index,
)
from leavers.forms import LeaverConfirmationForm, SearchForm
from leavers.utils import update_or_create_leaving_request  # /PS-IGNORE


class LeaverSearchView(View):
    form_class = SearchForm
    template_name = "leaving/line_manager/search.html"
    people_finder_search = get_people_finder_interface()

    def process_search(self, search_terms) -> List[ConsolidatedStaffDocument]:
        return consolidate_staff_documents(
            staff_documents=search_staff_index(query=search_terms),
        )

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
            if person["staff_sso_activity_stream_id"] == person_id:
                self.person: ConsolidatedStaffDocument = person
                break

        return super().dispatch(request, *args, **kwargs)

    def create_workflow(self):
        flow = Flow.objects.create(
            workflow_name="leaving",
            flow_name=f"{self.person['first_name']} {self.person['last_name']} is leaving",  # noqa E501
            executed_by=self.request.user,
        )
        flow.save()

        try:
            leaver_activitystream_user = ActivityStreamStaffSSOUser.objects.get(
                email_address=self.person["email_address"],
            )
        except ActivityStreamStaffSSOUser.DoesNotExist:
            raise Exception("Unable to find leaver in the Staff SSO ActivityStream.")

        update_or_create_leaving_request(
            leaver=leaver_activitystream_user,
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
