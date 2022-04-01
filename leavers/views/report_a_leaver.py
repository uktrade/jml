from datetime import datetime
from typing import Any, Optional, cast

from django.http.request import HttpRequest
from django.http.response import HttpResponseBase
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from activity_stream.models import ActivityStreamStaffSSOUser
from core.staff_search.forms import SearchForm
from core.staff_search.views import StaffSearchView
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    StaffDocument,
    consolidate_staff_documents,
    get_staff_document_from_staff_index,
)
from leavers.forms import leaver as leaver_forms
from leavers.models import LeavingRequest
from leavers.utils import (
    get_or_create_leaving_workflow,
    update_or_create_leaving_request,
)
from user.models import User

LEAVER_SEARCH_PARAM = "leaver_uuid"
MANAGER_SEARCH_PARAM = "manager_uuid"
LEAVER_SESSION_KEY = "leaver_uuid"
MANAGER_SESSION_KEY = "manager_uuid"


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
        self.leaving_request = get_object_or_404(
            LeavingRequest, uuid=kwargs["leaving_request_uuid"]
        )

        if LEAVER_SESSION_KEY in request.session:
            self.exclude_staff_ids = [
                self.leaving_request.leaver_activitystream_user.identifier
            ]
        return super().dispatch(request, *args, **kwargs)


class ConfirmationView(FormView):
    template_name = "leaving/report_a_leaver/confirm.html"
    form_class = leaver_forms.LeaverConfirmationForm
    success_url = reverse_lazy("report-a-leaver-request-received")

    def get_leaver(self, request):
        """
        Gets the leaver from the GET param.

        Sets the following values:
        - self.leaver
        - self.leaver_activitystream_user
        """

        user = cast(User, request.user)

        self.leaver: Optional[ConsolidatedStaffDocument] = None
        leaver_uuid: Optional[str] = request.GET.get(LEAVER_SEARCH_PARAM, None)

        # If there is a value in the session, we either want to use it or clear it.
        if LEAVER_SESSION_KEY in self.request.session:
            if leaver_uuid:
                del self.request.session[LEAVER_SESSION_KEY]
            else:
                leaver_uuid = request.session[LEAVER_SESSION_KEY]

        # If we don't have a leaver_uuid in the GET params, redirect back to search.
        if not leaver_uuid:
            redirect("report-a-leaver-search")

        # Load the leaver from the Staff index.
        leaver_staff_document: StaffDocument = get_staff_document_from_staff_index(
            staff_uuid=leaver_uuid
        )
        self.leaver: ConsolidatedStaffDocument = consolidate_staff_documents(
            staff_documents=[leaver_staff_document],
        )[0]
        request.session[LEAVER_SESSION_KEY] = leaver_uuid
        request.session.save()

        try:
            self.leaver_activitystream_user = ActivityStreamStaffSSOUser.objects.get(
                identifier=self.leaver["staff_sso_activity_stream_id"],
            )
        except ActivityStreamStaffSSOUser.DoesNotExist:
            raise Exception("Unable to find leaver in the Staff SSO ActivityStream.")

        self.leaving_request = update_or_create_leaving_request(
            leaver=self.leaver_activitystream_user,
            user_requesting=user,
        )

    def get_manager(self, request):
        """
        Gets the manager from the DB or the GET param.

        Sets the following values:
        - self.manager
        - self.manager_activitystream_user
        """

        manager_uuid: Optional[str] = request.GET.get(MANAGER_SEARCH_PARAM, None)
        manager_staff_document: Optional[StaffDocument] = None

        # If there is a value in the session, we either want to use it or clear it.
        if MANAGER_SESSION_KEY in request.session:
            if manager_uuid:
                # If the manager_uuid is in the GET params, clear the current
                # session value
                del request.session[MANAGER_SESSION_KEY]
            else:
                # If there is not manager_uuid in the GET params, use the current
                # session value
                manager_uuid = request.session[MANAGER_SESSION_KEY]

        # Try to load the manager using existing data from the database.
        if not manager_uuid and self.leaving_request.manager_activitystream_user:
            self.manager_activitystream_user = (
                self.leaving_request.manager_activitystream_user
            )
            manager_staff_document: StaffDocument = get_staff_document_from_staff_index(
                staff_id=self.leaving_request.manager_activitystream_user.identifier
            )

        # Load the manager from the Staff index (if we haven't managed to load it yet)
        if manager_uuid and not manager_staff_document:
            manager_staff_document: StaffDocument = get_staff_document_from_staff_index(
                staff_uuid=manager_uuid
            )

        # If we have a manager, we can create a ConsolidatedStaffDocument and
        # store data in the session.
        if manager_staff_document:
            self.manager: ConsolidatedStaffDocument = consolidate_staff_documents(
                staff_documents=[manager_staff_document],
            )[0]
            request.session[MANAGER_SESSION_KEY] = manager_uuid
            request.session.save()
            try:
                self.manager_activitystream_user = (
                    ActivityStreamStaffSSOUser.objects.get(
                        identifier=self.manager["staff_sso_activity_stream_id"],
                    )
                )
            except ActivityStreamStaffSSOUser.DoesNotExist:
                raise Exception(
                    "Unable to find manager in the Staff SSO ActivityStream."
                )

    def dispatch(self, request, *args, **kwargs):
        self.leaving_request: Optional[LeavingRequest] = None

        self.leaver: Optional[ConsolidatedStaffDocument] = None
        self.leaver_activitystream_user: Optional[ActivityStreamStaffSSOUser] = None
        self.get_leaver(request)

        self.manager: Optional[ConsolidatedStaffDocument] = None
        self.manager_activitystream_user: Optional[ActivityStreamStaffSSOUser] = None
        self.get_manager(request)

        return super().dispatch(request, *args, **kwargs)

    def create_workflow(self, last_day: datetime):
        assert self.leaver
        user = cast(User, self.request.user)

        flow = get_or_create_leaving_workflow(
            leaving_request=self.leaving_request,
            executed_by=user,
        )

        self.leaving_request = update_or_create_leaving_request(
            leaver=self.leaver_activitystream_user,
            manager_activitystream_user=self.manager_activitystream_user,
            user_requesting=user,
            flow=flow,
            last_day=last_day,
        )

    def form_valid(self, form):
        if not self.leaver_activitystream_user:
            raise Exception("No leaver selected.")
        if not self.manager_activitystream_user:
            raise Exception("No manager selected.")

        # TODO: Send Leaver Notifier Thank you email

        self.create_workflow(
            last_day=form.cleaned_data["last_day"],
        )
        # Need to validate user is correct record here
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            leaver=self.leaver,
            manager=self.manager,
            manager_search=reverse(
                "report-a-leaver-manager-search",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
            manager_search_form=SearchForm(),
        )
        return context


class RequestReceivedView(TemplateView):
    template_name = "leaving/report_a_leaver/request_received.html"
