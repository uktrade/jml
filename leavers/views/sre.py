from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple, Type, TypedDict, cast

from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models.query import QuerySet
from django.forms import Form
from django.http import Http404
from django.http.request import HttpRequest
from django.http.response import HttpResponseBase
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import FormView

from core.utils.helpers import DATE_FORMAT_STR, make_possessive
from core.views import BaseTemplateView
from leavers.forms.sre import (
    ServiceAndToolActions,
    SREAddTaskNoteForm,
    SREConfirmCompleteForm,
    SREServiceAndToolsForm,
)
from leavers.models import LeaverInformation, LeavingRequest, TaskLog
from leavers.views import base
from leavers.views.leaver import LeavingRequestViewMixin
from user.models import User


class IsSreUser(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(
            name="SRE",
        ).exists()


class SreViewMixin(IsSreUser, LeavingRequestViewMixin, BaseTemplateView):
    pass


class LeavingRequestListing(IsSreUser, base.LeavingRequestListing):
    template_name = "leaving/sre/listing.html"

    complete_field = "sre_complete"
    confirmation_view = "sre-detail"
    summary_view = "sre-summary"
    page_title = "SRE access removal"
    fields: List[Tuple[str, str]] = [
        ("leaver_name", "Leaver's name"),
        ("work_email", "Email"),
        ("last_working_day", "Last working day"),
        ("days_until_last_working_day", "Days left"),
        ("complete", "Status"),
    ]

    def get_leaving_requests(
        self,
        order_by: Optional[str] = None,
        order_direction: Literal["asc", "desc"] = "asc",
    ) -> QuerySet[LeavingRequest]:
        leaving_requests = super().get_leaving_requests(
            order_by=order_by,
            order_direction=order_direction,
        )
        # Filter out any that haven't been completed by the Line Manager.
        return leaving_requests.exclude(line_manager_complete__isnull=True)


class ServiceInfo(TypedDict):
    field_name: str
    name: str
    comment: str
    status_colour: Literal["green", "grey"]
    status_text: str


class TaskDetailView(SreViewMixin):
    template_name = "leaving/sre/task.html"
    page_title = "SRE access removal confirmation"
    back_link_url = reverse_lazy("sre-listing-incomplete")
    back_link_text = "Back to Leaving requests"

    def get_services(self) -> List[ServiceInfo]:
        services = []

        for service in self.leaving_request.sre_services():
            service_field, service_name, service_status = service

            service_info = ServiceInfo(
                field_name=service_field,
                name=service_name,
                comment="",
                status_colour="grey",
                status_text="To do",
            )

            if service_status == ServiceAndToolActions.NOT_STARTED:
                service_info["status_colour"] = "grey"
                service_info["status_text"] = "Not started"
            elif service_status == ServiceAndToolActions.NOT_APPLICABLE:
                service_info["status_colour"] = "grey"
                service_info["status_text"] = "N/A"
            elif service_status == ServiceAndToolActions.REMOVED:
                service_info["status_colour"] = "green"
                service_info["status_text"] = "Removed"

            service_field_task_log: Optional[TaskLog] = (
                self.leaving_request.task_logs.filter(
                    reference=f"LeavingRequest.{service_field}"
                )
                .order_by("-created_at")
                .first()
            )
            if service_field_task_log:
                if not service_field_task_log.value and service_field_task_log.notes:
                    service_info["comment"] = service_field_task_log.notes
                else:
                    created_at = service_field_task_log.created_at.strftime(
                        DATE_FORMAT_STR
                    )
                    if service_field_task_log.user:
                        service_info["comment"] = (
                            f"Last updated by {service_field_task_log.user.get_full_name()}"
                            f" on {created_at}"
                        )
                    else:
                        service_info["comment"] = f"Last updated at {created_at}"

            services.append(service_info)

        return services

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        leaving_datetime = self.leaving_request.get_leaving_date()
        leaving_date: Optional[datetime] = None
        if leaving_datetime:
            leaving_date = leaving_datetime.date()

        last_day_datetime = self.leaving_request.get_last_day()
        last_day: Optional[datetime] = None
        if last_day_datetime:
            last_day = last_day_datetime.date()

        leaver_information: Optional[
            LeaverInformation
        ] = self.leaving_request.leaver_information.first()

        leaver_job_title: Optional[str] = None
        if leaver_information:
            leaver_job_title = leaver_information.job_title

        can_mark_as_complete: bool = True
        for _, _, service_status in self.leaving_request.sre_services():
            if service_status not in [
                ServiceAndToolActions.NOT_APPLICABLE,
                ServiceAndToolActions.REMOVED,
            ]:
                can_mark_as_complete = False

        context.update(
            leaving_request_uuid=self.leaving_request.uuid,
            page_title=self.page_title,
            leaver_name=self.leaving_request.get_leaver_name(),
            leaver_email=self.leaving_request.get_leaver_email(),
            leaver_job_title=leaver_job_title,
            leaving_date=leaving_date,
            last_day=last_day,
            complete=bool(self.leaving_request.sre_complete),
            services=self.get_services(),
            can_mark_as_complete=can_mark_as_complete,
        )

        return context


class TaskServiceAndToolsView(SreViewMixin):
    template_name = "leaving/sre/task_services_and_tools.html"
    forms: Dict[str, Type[Form]] = {
        "update_status_form": SREServiceAndToolsForm,
        "add_note_form": SREAddTaskNoteForm,
    }
    success_viewname = "sre-detail"
    back_link_viewname = "sre-detail"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        self.field_name = self.kwargs.get("field_name", None)
        if not self.field_name:
            raise Http404

        # Get service info
        sre_services = self.leaving_request.sre_services()
        self.service_name = None

        for sre_service in sre_services:
            if sre_service[0] == self.field_name:
                self.service_name = sre_service[1]

        if not self.service_name:
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get_page_title(self) -> str:
        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name: str = ""
        if leaver_name:
            possessive_leaver_name = make_possessive(leaver_name)
        return f"{possessive_leaver_name} SRE offboarding"

    def post_update_status_form(
        self, request: HttpRequest, form: Form, *args, **kwargs
    ):
        user = cast(User, request.user)

        action_value = form.cleaned_data["action"]
        action = ServiceAndToolActions(action_value)

        current_task_log: Optional[TaskLog] = getattr(
            self.leaving_request, self.field_name
        )
        if not current_task_log or (
            current_task_log and current_task_log.value != action.value
        ):
            task_log = self.leaving_request.task_logs.create(
                user=user,
                task_name=f"{self.field_name} has been updated to '{action.value}'",
                notes=f"Updated the status to '{action.label}'",
                reference=f"LeavingRequest.{self.field_name}",
                value=action.value,
            )
            setattr(
                self.leaving_request,
                self.field_name,
                task_log,
            )
            self.leaving_request.save()

        return redirect(self.get_success_url())

    def post_add_note_form(self, request: HttpRequest, form: Form, *args, **kwargs):
        note = form.cleaned_data["note"]

        user = cast(User, request.user)

        self.leaving_request.task_logs.create(
            user=user,
            task_name="A comment has been added.",
            notes=note,
            reference=f"LeavingRequest.{self.field_name}",
        )

        return redirect(
            self.get_view_url("sre-service-and-tools", field_name=self.field_name)
        )

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if "form_name" in request.POST:
            form_name = request.POST["form_name"]
            if form_name in self.forms:

                form = self.forms[form_name](request.POST)
                if form.is_valid():
                    # Call the "post_{form_name}" method to handle the form POST logic.
                    return getattr(self, f"post_{form_name}")(
                        request, form, *args, **kwargs
                    )
                else:
                    context[form_name] = form
        return self.render_to_response(context)

    def get_initial_update_status_form(self) -> Dict[str, Any]:
        initial = {}

        current_task_log: Optional[TaskLog] = getattr(
            self.leaving_request, self.field_name
        )
        if current_task_log:
            initial["action"] = current_task_log.value

        return initial

    def get_initial_add_note_form(self) -> Dict[str, Any]:
        initial: Dict[str, Any] = {}
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add form instances to the context.
        for form_name, form_class in self.forms.items():
            form_initial = getattr(self, f"get_initial_{form_name}")()
            context[form_name] = form_class(initial=form_initial)

        leaving_datetime = self.leaving_request.get_leaving_date()
        leaving_date: Optional[datetime] = None
        if leaving_datetime:
            leaving_date = leaving_datetime.date()

        last_day_datetime = self.leaving_request.get_last_day()
        last_day: Optional[datetime] = None
        if last_day_datetime:
            last_day = last_day_datetime.date()

        leaver_information: Optional[
            LeaverInformation
        ] = self.leaving_request.leaver_information.first()

        leaver_job_title: Optional[str] = None
        if leaver_information:
            leaver_job_title = leaver_information.job_title

        context.update(
            leaving_request_uuid=self.leaving_request.uuid,
            page_title=self.get_page_title(),
            leaver_name=self.leaving_request.get_leaver_name(),
            leaver_email=self.leaving_request.get_leaver_email(),
            leaver_job_title=leaver_job_title,
            leaving_date=leaving_date,
            last_day=last_day,
            complete=bool(self.leaving_request.sre_complete),
            service_name=self.service_name,
            task_notes=self.leaving_request.get_sre_notes(field_name=self.field_name),
        )

        return context


class TaskCompleteConfirmationView(SreViewMixin, FormView):
    template_name = "leaving/sre/task_confirmation.html"
    form_class = SREConfirmCompleteForm
    success_viewname = "sre-summary"
    back_link_viewname = "sre-detail"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        if self.leaving_request.sre_complete:
            return redirect(self.get_success_url())

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(leaving_request_uuid=self.leaving_request.uuid)

        return form_kwargs

    def get_page_title(self) -> str:
        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name: str = ""
        if leaver_name:
            possessive_leaver_name = make_possessive(leaver_name)
        return f"{possessive_leaver_name} SRE offboarding: confirm record is complete"

    def form_valid(self, form):
        from core.utils.sre_messages import send_sre_complete_message

        response = super().form_valid(form)

        self.leaving_request.sre_complete = timezone.now()
        self.leaving_request.save(update_fields=["sre_complete"])

        if settings.APP_ENV == "production":
            send_sre_complete_message(
                leaving_request=self.leaving_request,
            )

        return response

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name: str = ""
        if leaver_name:
            possessive_leaver_name = make_possessive(leaver_name)

        context.update(
            leaving_request_uuid=self.leaving_request.uuid,
            page_title=self.get_page_title(),
            possessive_leaver_name=possessive_leaver_name,
        )
        return context


class TaskSummaryView(SreViewMixin):
    template_name = "leaving/sre/summary.html"
    page_title: str = "SRE access removal summary"
    back_link_url = reverse_lazy("sre-listing-complete")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(page_title=self.page_title)

        access_removed_services: List[Tuple[str, str, TaskLog]] = [
            (
                sre_service[0],
                sre_service[1],
                getattr(self.leaving_request, sre_service[0]),
            )
            for sre_service in self.leaving_request.sre_services()
            if sre_service[2] == ServiceAndToolActions.REMOVED
        ]
        context.update(
            leaver_name=self.leaving_request.get_leaver_name(),
            access_removed_services=access_removed_services,
        )

        return context


class ThankYouView(SreViewMixin):
    template_name = "leaving/sre/thank_you.html"
    page_title: str = "SRE access removal thank you"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        manager_as_user = self.leaving_request.get_line_manager()
        assert manager_as_user

        context.update(
            page_title=self.page_title,
            leaving_request_uuid=self.leaving_request.uuid,
            leaver_name=self.leaving_request.get_leaver_name(),
            line_manager_name=manager_as_user.full_name,
            leaving_request=self.leaving_request,
            access_removed_services=[
                sre_service[1]
                for sre_service in self.leaving_request.sre_services()
                if sre_service[2] == ServiceAndToolActions.REMOVED
            ],
            complete=bool(self.leaving_request.sre_complete),
        )

        return context
