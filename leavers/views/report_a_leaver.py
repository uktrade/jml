from datetime import datetime
from typing import Any, Optional, cast

from django.core.exceptions import PermissionDenied
from django.http.request import HttpRequest
from django.http.response import HttpResponseBase
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django_workflow_engine.exceptions import WorkflowNotAuthError
from django_workflow_engine.executor import WorkflowExecutor
from django_workflow_engine.models import Flow

from activity_stream.models import ActivityStreamStaffSSOUser
from core.staff_search.forms import SearchForm
from core.staff_search.views import StaffSearchView
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    StaffDocument,
    consolidate_staff_documents,
    get_staff_document_from_staff_index,
)
from leavers.forms import LeaverConfirmationForm
from leavers.utils import update_or_create_leaving_request  # /PS-IGNORE
from user.models import User

LEAVER_SEARCH_PARAM = "leaver_id"
MANAGER_SEARCH_PARAM = "manager_id"
LEAVER_SESSION_KEY = "leaver_id"
MANAGER_SESSION_KEY = "manager_id"


class LeaverSearchView(StaffSearchView):
    success_url = reverse_lazy("report-a-leaver-confirmation")
    search_name = "leaver"
    query_param_name = LEAVER_SEARCH_PARAM

    def dispatch(self, request, *args, **kwargs):
        if LEAVER_SESSION_KEY in self.request.session:
            del self.request.session[LEAVER_SESSION_KEY]
        if MANAGER_SESSION_KEY in self.request.session:
            del self.request.session[MANAGER_SESSION_KEY]
        return super().dispatch(request, *args, **kwargs)


class ManagerSearchView(StaffSearchView):
    success_url = reverse_lazy("report-a-leaver-confirmation")
    search_name = "manager"
    query_param_name = MANAGER_SEARCH_PARAM

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        if LEAVER_SESSION_KEY in request.session:
            self.exclude_staff_ids = [request.session[LEAVER_SESSION_KEY]]
        return super().dispatch(request, *args, **kwargs)


class ConfirmationView(FormView):
    template_name = "leaving/line_manager/confirm.html"
    form_class = LeaverConfirmationForm
    success_url = reverse_lazy("report-a-leaver-request-received")

    def dispatch(self, request, *args, **kwargs):
        self.leaver: Optional[ConsolidatedStaffDocument] = None
        self.manager: Optional[ConsolidatedStaffDocument] = None

        # Get the learner
        leaver_id: Optional[str] = request.GET.get(LEAVER_SEARCH_PARAM, None)
        if LEAVER_SESSION_KEY in self.request.session:
            leaver_id = self.request.session[LEAVER_SESSION_KEY]
        if not leaver_id:
            redirect("report-a-leaver-search")
        else:
            leaver_staff_document: StaffDocument = get_staff_document_from_staff_index(
                staff_id=leaver_id
            )
            self.leaver: ConsolidatedStaffDocument = consolidate_staff_documents(
                staff_documents=[leaver_staff_document],
            )[0]
            self.request.session[LEAVER_SESSION_KEY] = leaver_id
            self.request.session.save()

        # Get the manager
        manager_id: Optional[str] = request.GET.get(MANAGER_SEARCH_PARAM, None)
        if MANAGER_SESSION_KEY in self.request.session:
            manager_id = self.request.session[MANAGER_SESSION_KEY]
        if manager_id:
            manager_staff_document: StaffDocument = get_staff_document_from_staff_index(
                staff_id=manager_id
            )
            self.manager: ConsolidatedStaffDocument = consolidate_staff_documents(
                staff_documents=[manager_staff_document],
            )[0]
            self.request.session[MANAGER_SESSION_KEY] = manager_id
            self.request.session.save()

        return super().dispatch(request, *args, **kwargs)

    def create_workflow(self, last_day: datetime):
        assert self.leaver
        assert self.manager

        flow = Flow.objects.create(
            workflow_name="leaving",
            flow_name=f"{self.leaver['first_name']} {self.leaver['last_name']} is leaving",  # noqa E501
            executed_by=self.request.user,
        )
        flow.save()

        try:
            leaver_activitystream_user = ActivityStreamStaffSSOUser.objects.get(
                identifier=self.leaver["staff_sso_activity_stream_id"],
            )
        except ActivityStreamStaffSSOUser.DoesNotExist:
            raise Exception("Unable to find leaver in the Staff SSO ActivityStream.")
        try:
            manager_activitystream_user = ActivityStreamStaffSSOUser.objects.get(
                identifier=self.manager["staff_sso_activity_stream_id"],
            )
        except ActivityStreamStaffSSOUser.DoesNotExist:
            raise Exception("Unable to find manager in the Staff SSO ActivityStream.")

        user = cast(User, self.request.user)

        update_or_create_leaving_request(
            leaver=leaver_activitystream_user,
            manager_activitystream_user=manager_activitystream_user,
            user_requesting=user,
            flow=flow,
            leaver_first_name=self.leaver["first_name"],
            leaver_last_name=self.leaver["last_name"],
            last_day=last_day,
        )

        executor = WorkflowExecutor(flow)

        try:
            executor.run_flow(user=self.request.user)
        except WorkflowNotAuthError as e:
            raise PermissionDenied(f"{e}")

    def form_valid(self, form):
        self.create_workflow(
            last_day=form.cleaned_data["last_day"],
        )
        # Need to validate user is correct record here
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["leaver"] = self.leaver
        context["manager"] = self.manager
        context["manager_search"] = reverse("report-a-leaver-manager-search")
        context["manager_search_form"] = SearchForm()
        return context


class RequestReceivedView(TemplateView):
    template_name = "leaving/line_manager/request_received.html"
