from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, cast

from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from leavers.forms.security_team import (
    BuildingPassDestroyedForm,
    BuildingPassDisabledForm,
    BuildingPassNotReturnedForm,
    BuildingPassReturnedForm,
    RosaKit,
    RosaKitCloseRecordForm,
    RosaKitForm,
)
from leavers.models import LeavingRequest, TaskLog
from leavers.utils.security_team import (
    SecuritySubRole,
    get_security_role,
    set_security_role,
)
from leavers.views import base
from user.models import User


class LeavingRequestListing(base.LeavingRequestListing):
    template_name = "leaving/security_team/listing.html"

    building_pass_confirmation_view = "security-team-building-pass-confirmation"
    rosa_kit_confirmation_view = "security-team-rosa-kit-confirmation"
    summary_view = "security-team-summary"

    def test_func(self):
        return self.request.user.groups.filter(
            name="Security Team",
        ).exists()

    def get_leaving_requests(self) -> QuerySet[LeavingRequest]:
        leaving_requests = super().get_leaving_requests()
        # Filter out any that haven't been completed by the Line Manager.
        return leaving_requests.exclude(line_manager_complete__isnull=True)

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.role = get_security_role(request)
        return super().dispatch(request, *args, **kwargs)

    def get_page_title(self, object_type_name: str) -> str:
        if self.role == SecuritySubRole.BUILDING_PASS:
            return f"Building Pass: {object_type_name.title()}"
        elif self.role == SecuritySubRole.ROSA_KIT:
            return f"ROSA Kit: {object_type_name.title()}"
        raise Exception("Unknown security role")

    def get_service_name(self) -> str:
        if self.role == SecuritySubRole.BUILDING_PASS:
            return "Leaving DIT: Building pass actions"
        elif self.role == SecuritySubRole.ROSA_KIT:
            return "Leaving DIT: ROSA Kit actions"

        raise Exception("Unknown security role")

    def get_complete_field(self) -> str:
        if self.role == SecuritySubRole.BUILDING_PASS:
            return "security_team_building_pass_complete"
        elif self.role == SecuritySubRole.ROSA_KIT:
            return "security_team_rosa_kit_complete"

        raise Exception("Unknown security role")

    def get_confirmation_view(self) -> str:
        if self.role == SecuritySubRole.BUILDING_PASS:
            return self.building_pass_confirmation_view
        elif self.role == SecuritySubRole.ROSA_KIT:
            return self.rosa_kit_confirmation_view

        raise Exception("Unknown security role")


class BuildingPassConfirmationView(
    UserPassesTestMixin,
    TemplateView,
):
    template_name = "leaving/security_team/confirmation/building_pass.html"
    page_title: str = "Security Team off-boarding building pass confirmation"

    def test_func(self):
        return self.request.user.groups.filter(
            name="Security Team",
        ).exists()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        set_security_role(request=request, role=SecuritySubRole.BUILDING_PASS)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            page_title=self.page_title,
        )

        notes: Optional[str] = None
        if self.leaving_request.security_pass_not_returned:
            notes = self.leaving_request.security_pass_not_returned.notes

        manager_as_user = self.leaving_request.get_line_manager()
        assert manager_as_user

        leaving_datetime = self.leaving_request.get_leaving_date()
        leaving_date: Optional[datetime] = None
        if leaving_datetime:
            leaving_date = leaving_datetime.date()

        last_day_datetime = self.leaving_request.get_last_day()
        last_day: Optional[datetime] = None
        if last_day_datetime:
            last_day = last_day_datetime.date()

        context.update(
            leaver_name=self.leaving_request.get_leaver_name(),
            leaver_email=self.leaving_request.get_leaver_email(),
            manager_name=manager_as_user.full_name,
            manager_emails=manager_as_user.get_email_addresses_for_contact(),
            leaving_date=leaving_date,
            last_working_day=last_day,
            leaving_request_uuid=self.leaving_request.uuid,
            notifications=self.get_notifications(),
            pass_disabled=bool(self.leaving_request.security_pass_disabled),
            pass_returned=bool(self.leaving_request.security_pass_returned),
            pass_destroyed=bool(self.leaving_request.security_pass_destroyed),
            pass_not_returned=bool(self.leaving_request.security_pass_not_returned),
            can_mark_as_not_returned=bool(
                self.leaving_request.leaving_date < timezone.now()
                and not self.leaving_request.security_team_building_pass_complete
            ),
            notes=notes,
        )

        return context

    def get_notifications(self) -> List[Dict[str, Any]]:
        notifications = []

        notification_email_mapping = {
            "two_days_after_lwd": (
                "2 days after last working day reminder email to the Line Manager"
            ),
            "on_ld": "On leaving date reminder email to the Line Manager",
            "one_day_after_ld": (
                "1 day after leaving date reminder email to the Line Manager"
            ),
            "two_days_after_ld_lm": (
                "2 days after leaving date reminder email to the Line Manager"
            ),
        }
        email_tasks = self.leaving_request.get_security_bp_reminder_email_tasks()

        for key, task_logs in email_tasks.items():
            task_logs = cast(List[TaskLog], task_logs)
            if key in notification_email_mapping:
                last_sent: Optional[datetime] = None
                for task_log in task_logs:
                    if not last_sent or last_sent < task_log.created_at:
                        last_sent = task_log.created_at

                notifications.append(
                    {
                        "sent": bool(task_logs),
                        "name": notification_email_mapping[key],
                        "last_sent": last_sent,
                    }
                )

        return notifications


class BuildingPassDisabledView(
    UserPassesTestMixin,
    FormView,
):
    template_name = "leaving/security_team/confirmation/building_pass_action.html"
    page_title: str = "Security Team off-boarding: Building pass disabled confirmation"
    form_class = BuildingPassDisabledForm

    def test_func(self):
        return self.request.user.groups.filter(
            name="Security Team",
        ).exists()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse_lazy(
            "security-team-building-pass-confirmation", args=[self.leaving_request.uuid]
        )

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(leaving_request_uuid=self.leaving_request.uuid)

        return form_kwargs

    def form_valid(self, form):
        user = cast(User, self.request.user)

        self.leaving_request.security_pass_disabled = (
            self.leaving_request.task_logs.create(
                user=user,
                task_name="Building pass disabled",
            )
        )
        self.leaving_request.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            leaving_request_uuid=self.leaving_request.uuid,
            page_title=self.page_title,
            action_name="disabled",
        )
        return context


class BuildingPassReturnedView(
    UserPassesTestMixin,
    FormView,
):
    template_name = "leaving/security_team/confirmation/building_pass_action.html"
    page_title: str = "Security Team off-boarding: Building pass returned confirmation"
    form_class = BuildingPassReturnedForm

    def test_func(self):
        return self.request.user.groups.filter(
            name="Security Team",
        ).exists()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse_lazy(
            "security-team-building-pass-confirmation", args=[self.leaving_request.uuid]
        )

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(leaving_request_uuid=self.leaving_request.uuid)

        return form_kwargs

    def form_valid(self, form):
        user = cast(User, self.request.user)

        self.leaving_request.security_pass_returned = (
            self.leaving_request.task_logs.create(
                user=user,
                task_name="Building pass returned",
            )
        )
        self.leaving_request.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            leaving_request_uuid=self.leaving_request.uuid,
            page_title=self.page_title,
            action_name="disabled",
        )
        return context


class BuildingPassDestroyedView(
    UserPassesTestMixin,
    FormView,
):
    template_name = "leaving/security_team/confirmation/building_pass_action.html"
    page_title: str = "Security Team off-boarding: Building pass destroyed confirmation"
    form_class = BuildingPassDestroyedForm

    def test_func(self):
        return self.request.user.groups.filter(
            name="Security Team",
        ).exists()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse_lazy("security-team-summary", args=[self.leaving_request.uuid])

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(leaving_request_uuid=self.leaving_request.uuid)

        return form_kwargs

    def form_valid(self, form):
        user = cast(User, self.request.user)

        self.leaving_request.security_pass_destroyed = (
            self.leaving_request.task_logs.create(
                user=user,
                task_name="Building pass destroyed",
            )
        )
        self.leaving_request.security_team_building_pass_complete = timezone.now()
        self.leaving_request.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            leaving_request_uuid=self.leaving_request.uuid,
            page_title=self.page_title,
            action_name="destroyed",
        )
        return context


class BuildingPassNotReturnedView(
    UserPassesTestMixin,
    FormView,
):
    template_name = "leaving/security_team/confirmation/building_pass_action.html"
    page_title: str = (
        "Security Team off-boarding: Building pass not returned confirmation"
    )
    form_class = BuildingPassNotReturnedForm

    def test_func(self):
        return self.request.user.groups.filter(
            name="Security Team",
        ).exists()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse_lazy(
            "security-team-building-pass-confirmation", args=[self.leaving_request.uuid]
        )

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(leaving_request_uuid=self.leaving_request.uuid)

        return form_kwargs

    def form_valid(self, form):
        user = cast(User, self.request.user)

        self.leaving_request.security_pass_not_returned = (
            self.leaving_request.task_logs.create(
                user=user,
                task_name="Building pass not returned",
                notes=form.cleaned_data.get("notes", ""),
            )
        )
        self.leaving_request.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            leaving_request_uuid=self.leaving_request.uuid,
            page_title=self.page_title,
            action_name="not returned",
        )
        return context


class RosaKitConfirmationView(
    UserPassesTestMixin,
    FormView,
):
    template_name = "leaving/security_team/confirmation/rosa_kit.html"
    page_title: str = "Security Team off-boarding ROSA kit confirmation"
    form_class = RosaKitForm

    def get_success_url(self) -> str:
        return reverse_lazy("security-team-summary", args=[self.leaving_request.uuid])

    def test_func(self):
        return self.request.user.groups.filter(
            name="Security Team",
        ).exists()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        set_security_role(request=request, role=SecuritySubRole.ROSA_KIT)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            page_title=self.page_title,
        )

        manager_as_user = self.leaving_request.get_line_manager()
        assert manager_as_user

        leaving_datetime = self.leaving_request.get_leaving_date()
        leaving_date: Optional[datetime] = None
        if leaving_datetime:
            leaving_date = leaving_datetime.date()

        last_day_datetime = self.leaving_request.get_last_day()
        last_day: Optional[datetime] = None
        if last_day_datetime:
            last_day = last_day_datetime.date()

        context.update(
            leaver_name=self.leaving_request.get_leaver_name(),
            leaver_email=self.leaving_request.get_leaver_email(),
            manager_name=manager_as_user.full_name,
            manager_emails=manager_as_user.get_email_addresses_for_contact(),
            leaving_date=leaving_date,
            last_working_day=last_day,
            leaving_request_uuid=self.leaving_request.uuid,
            notifications=self.get_notifications(),
        )

        return context

    def get_notifications(self) -> List[Dict[str, Any]]:
        notifications = []

        notification_email_mapping = {
            "two_days_after_lwd": (
                "2 days after last working day reminder email to the Line Manager"
            ),
            "on_ld": "On leaving date reminder email to the Line Manager",
            "one_day_after_ld": "1 day after leaving date reminder email to the Line Manager",
            "two_days_after_ld_lm": " 2 days after leaving date reminder email to the Line Manager",
        }
        email_tasks = self.leaving_request.get_security_rk_reminder_email_tasks()

        for key, task_logs in email_tasks.items():
            task_logs = cast(List[TaskLog], task_logs)
            if key in notification_email_mapping:
                last_sent: Optional[datetime] = None
                for task_log in task_logs:
                    if not last_sent or last_sent < task_log.created_at:
                        last_sent = task_log.created_at

                notifications.append(
                    {
                        "sent": bool(task_logs),
                        "name": notification_email_mapping[key],
                        "last_sent": last_sent,
                    }
                )

        return notifications

        return notifications

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        if self.leaving_request.rosa_kit_form_data:
            initial.update(**self.leaving_request.rosa_kit_form_data)
        return initial

    def form_valid(self, form):
        user = cast(User, self.request.user)
        self.leaving_request.rosa_kit_form_data = form.cleaned_data

        submission_type: Literal["close", "save"] = "save"
        if "save" in form.data:
            submission_type = "save"
        elif "close" in form.data:
            submission_type = "close"
            if RosaKit.MOBILE.value in form.cleaned_data["user_returned"]:
                self.leaving_request.rosa_mobile_returned = (
                    self.leaving_request.task_logs.create(
                        user=user,
                        task_name="ROSA Mobile returned",
                    )
                )
            if RosaKit.LAPTOP.value in form.cleaned_data["user_returned"]:
                self.leaving_request.rosa_laptop_returned = (
                    self.leaving_request.task_logs.create(
                        user=user,
                        task_name="ROSA Laptop returned",
                    )
                )
            if RosaKit.KEY.value in form.cleaned_data["user_returned"]:
                self.leaving_request.rosa_key_returned = (
                    self.leaving_request.task_logs.create(
                        user=user,
                        task_name="ROSA Key returned",
                    )
                )

        self.leaving_request.save()

        if submission_type == "save":
            return redirect(
                reverse(
                    "security-team-rosa-kit-confirmation",
                    kwargs={"leaving_request_id": self.leaving_request.uuid},
                )
            )
        elif submission_type == "close":
            return redirect(
                reverse(
                    "security-team-rosa-kit-confirmation-close",
                    kwargs={"leaving_request_id": self.leaving_request.uuid},
                )
            )
        return super().form_valid(form)


class RosaKitConfirmationCloseView(
    UserPassesTestMixin,
    FormView,
):
    template_name = "leaving/security_team/confirmation/rosa_kit_action.html"
    page_title: str = "Security Team off-boarding: ROSA Kit confirmation"
    form_class = RosaKitCloseRecordForm

    def test_func(self):
        return self.request.user.groups.filter(
            name="Security Team",
        ).exists()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse_lazy("security-team-summary", args=[self.leaving_request.uuid])

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(leaving_request_uuid=self.leaving_request.uuid)

        return form_kwargs

    def form_valid(self, form):
        self.leaving_request.security_team_rosa_kit_complete = timezone.now()
        self.leaving_request.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            leaving_request_uuid=self.leaving_request.uuid,
            page_title=self.page_title,
        )
        return context


class TaskSummaryView(
    UserPassesTestMixin,
    TemplateView,
):
    template_name = "leaving/security_team/summary.html"
    page_title: str = "Security Team off-boarding summary"

    def test_func(self):
        return self.request.user.groups.filter(
            name="Security Team",
        ).exists()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_rosa_kit_statuses(self):
        rosa_kit_statuses = {
            RosaKit.MOBILE.value: {
                "colour": "blue",
                "text": "Pending",
            },
            RosaKit.LAPTOP.value: {
                "colour": "blue",
                "text": "Pending",
            },
            RosaKit.KEY.value: {
                "colour": "blue",
                "text": "Pending",
            },
        }

        user_has = []
        user_returned = []
        if self.leaving_request.rosa_kit_form_data:
            user_has = self.leaving_request.rosa_kit_form_data["user_has"]
            user_returned = self.leaving_request.rosa_kit_form_data["user_has"]

        for key, status in rosa_kit_statuses.items():
            if key not in user_has:
                status["colour"] = "yellow"
                status["text"] = "Leaver doesn't have"

            if key in user_returned:
                status["colour"] = "green"
                status["text"] = "Returned"

        return rosa_kit_statuses

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            page_title=self.page_title,
        )

        building_pass_notes: Optional[str] = None
        if self.leaving_request.security_pass_not_returned:
            building_pass_notes = self.leaving_request.security_pass_not_returned.notes

        rosa_kit_statuses = self.get_rosa_kit_statuses()
        rosa_kit_tasks = []

        rosa_kit_tasks.append(
            {
                "name": "Retrieve ROSA Mobile",
                "status": rosa_kit_statuses[RosaKit.MOBILE.value],
            }
        )
        rosa_kit_tasks.append(
            {
                "name": "Retrieve ROSA Laptop",
                "status": rosa_kit_statuses[RosaKit.LAPTOP.value],
            }
        )
        rosa_kit_tasks.append(
            {
                "name": "Retrieve ROSA Key",
                "status": rosa_kit_statuses[RosaKit.KEY.value],
            }
        )

        rosa_kit_notes = None
        if self.leaving_request.rosa_kit_form_data:
            rosa_kit_notes = self.leaving_request.rosa_kit_form_data.get("notes")

        context.update(
            leaver_name=self.leaving_request.get_leaver_name(),
            leaving_request_uuid=self.leaving_request.uuid,
            pass_disabled=self.leaving_request.security_pass_disabled,
            pass_returned=self.leaving_request.security_pass_returned,
            pass_destroyed=self.leaving_request.security_pass_destroyed,
            pass_not_returned=self.leaving_request.security_pass_not_returned,
            building_pass_notes=building_pass_notes,
            rosa_kit_tasks=rosa_kit_tasks,
            rosa_kit_complete=bool(
                self.leaving_request.security_team_rosa_kit_complete
            ),
            rosa_kit_notes=rosa_kit_notes,
        )

        return context
