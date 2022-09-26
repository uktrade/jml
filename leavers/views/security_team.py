from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from leavers.forms.security_team import (
    AddTaskNoteForm,
    RosaKit,
    RosaKitCloseRecordForm,
    RosaKitForm,
)
from leavers.models import LeavingRequest, TaskLog
from leavers.types import SecurityClearance
from leavers.utils.security_team import (
    SecuritySubRole,
    get_security_role,
    set_security_role,
)
from leavers.views import base
from user.models import User


class LeavingRequestListing(base.LeavingRequestListing):
    template_name = "leaving/security_team/listing.html"

    fields: List[str] = [
        "leaver_name",
        "security_clearance",
        "work_email",
        "leaving_date",
        "last_working_day",
        "days_until_last_working_day",
        "complete",
    ]

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
    FormView,
):
    template_name = "leaving/security_team/confirmation/building_pass.html"
    form_class = AddTaskNoteForm

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

        leaver_name = self.leaving_request.get_leaver_name()
        context.update(page_title=f"{leaver_name} building pass")

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
            leaver_name=leaver_name,
            leaver_email=self.leaving_request.get_leaver_email(),
            leaver_security_clearance=SecurityClearance(
                self.leaving_request.security_clearance
            ).label,
            manager_name=manager_as_user.full_name,
            manager_emails=manager_as_user.get_email_addresses_for_contact(),
            leaving_date=leaving_date,
            last_working_day=last_day,
            leaving_request_uuid=self.leaving_request.uuid,
            pass_disabled=bool(self.leaving_request.security_pass_disabled),
            pass_returned=bool(self.leaving_request.security_pass_returned),
            pass_destroyed=bool(self.leaving_request.security_pass_destroyed),
            pass_not_returned=bool(self.leaving_request.security_pass_not_returned),
            can_mark_as_not_returned=bool(
                self.leaving_request.leaving_date < timezone.now()
                and not self.leaving_request.security_team_building_pass_complete
            ),
            complete=bool(self.leaving_request.security_team_building_pass_complete),
            task_notes=self.leaving_request.get_security_building_pass_notes(),
        )

        return context

    def get_success_url(self) -> str:
        return reverse(
            "security-team-building-pass-confirmation", args=[self.leaving_request.uuid]
        )

    def form_valid(self, form) -> HttpResponse:
        note = form.cleaned_data["note"]

        self.leaving_request.task_logs.create(
            user=self.request.user,
            task_name="A comment has been added.",
            notes=note,
            reference="LeavingRequest.security_team_building_pass_complete",
        )
        return super().form_valid(form)


# def mark_buidling_pass_disabled():
#     self.leaving_request.security_pass_disabled = (
#         self.leaving_request.task_logs.create(
#             user=user,
#             task_name="Building pass disabled",
#             reference="LeavingRequest.security_pass_disabled",
#         )
#     )
#     self.leaving_request.save()

# def mark_building_pass_returned():
#     self.leaving_request.security_pass_returned = (
#         self.leaving_request.task_logs.create(
#             user=user,
#             task_name="Building pass returned",
#             reference="LeavingRequest.security_pass_returned",
#         )
#     )
#     self.leaving_request.save()

# def mark_buidling_pass_destroyed():
#     self.leaving_request.security_pass_destroyed = (
#         self.leaving_request.task_logs.create(
#             user=user,
#             task_name="Building pass destroyed",
#             reference="LeavingRequest.security_pass_destroyed",
#         )
#     )
#     self.leaving_request.security_team_building_pass_complete = timezone.now()
#     self.leaving_request.save()

# def mark_buidling_pass_not_returned():
#     self.leaving_request.security_pass_not_returned = (
#         self.leaving_request.task_logs.create(
#             user=user,
#             task_name="Building pass not returned",
#             reference="LeavingRequest.security_pass_not_returned",
#             notes=form.cleaned_data.get("notes", ""),
#         )
#     )
#     self.leaving_request.save()


def get_rosa_kit_statuses(leaving_request: LeavingRequest) -> Dict[str, Dict[str, str]]:
    if not leaving_request.is_rosa_user:
        return {}

    rosa_kit_statuses: Dict[str, Dict[str, str]] = {
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
    if leaving_request.rosa_kit_form_data:
        user_has = leaving_request.rosa_kit_form_data["user_has"]
        user_returned = leaving_request.rosa_kit_form_data["user_returned"]

        for key, status in rosa_kit_statuses.items():
            if key in user_has:
                status["colour"] = "yellow"
                status["text"] = "Leaver has"

            if key in user_returned:
                status["colour"] = "green"
                status["text"] = "Returned"

    return rosa_kit_statuses


class RosaKitConfirmationView(
    UserPassesTestMixin,
    FormView,
):
    template_name = "leaving/security_team/confirmation/rosa_kit.html"
    form_class = AddTaskNoteForm

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

        leaver_name = self.leaving_request.get_leaver_name()
        context.update(page_title=f"{leaver_name} ROSA Kit")

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
            leaver_name=leaver_name,
            leaver_email=self.leaving_request.get_leaver_email(),
            leaver_security_clearance=SecurityClearance(
                self.leaving_request.security_clearance
            ).label,
            manager_name=manager_as_user.full_name,
            manager_emails=manager_as_user.get_email_addresses_for_contact(),
            leaving_date=leaving_date,
            last_working_day=last_day,
            leaving_request_uuid=self.leaving_request.uuid,
            task_notes=self.leaving_request.get_security_rosa_kit_notes(),
        )

        rosa_kit_statuses = get_rosa_kit_statuses(leaving_request=self.leaving_request)
        if rosa_kit_statuses:
            rosa_mobile_status = rosa_kit_statuses[RosaKit.MOBILE.value]["text"]
            rosa_laptop_status = rosa_kit_statuses[RosaKit.LAPTOP.value]["text"]
            rosa_key_status = rosa_kit_statuses[RosaKit.KEY.value]["text"]

            context.update(
                rosa_mobile_status=rosa_mobile_status,
                rosa_laptop_status=rosa_laptop_status,
                rosa_key_status=rosa_key_status,
            )

        return context

    def get_success_url(self) -> str:
        return reverse(
            "security-team-rosa-kit-confirmation", args=[self.leaving_request.uuid]
        )

    def form_valid(self, form) -> HttpResponse:
        note = form.cleaned_data["note"]

        self.leaving_request.task_logs.create(
            user=self.request.user,
            task_name="A comment has been added.",
            notes=note,
            reference="LeavingRequest.security_team_rosa_kit_complete",
        )
        return super().form_valid(form)


class RosaKitConfirmationEditView(
    UserPassesTestMixin,
    FormView,
):
    template_name = "leaving/security_team/confirmation/rosa_kit_edit.html"
    page_title: str = "Security Team offboarding ROSA kit confirmation"
    form_class = RosaKitForm

    def get_success_url(self) -> str:
        return reverse_lazy(
            "security-team-rosa-kit-confirmation", args=[self.leaving_request.uuid]
        )

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
            leaver_security_clearance=SecurityClearance(
                self.leaving_request.security_clearance
            ).label,
            manager_name=manager_as_user.full_name,
            manager_emails=manager_as_user.get_email_addresses_for_contact(),
            leaving_date=leaving_date,
            last_working_day=last_day,
            leaving_request_uuid=self.leaving_request.uuid,
        )

        return context

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(leaving_request_uuid=self.leaving_request.uuid)

        return form_kwargs

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        if self.leaving_request.rosa_kit_form_data:
            initial.update(**self.leaving_request.rosa_kit_form_data)
        return initial

    def form_valid(self, form):
        user = cast(User, self.request.user)
        self.leaving_request.rosa_kit_form_data = form.cleaned_data

        user_returned: List[str] = form.cleaned_data.get("user_returned", [])

        rosa_values_mapping: Dict[str, str] = {
            RosaKit.MOBILE.value: "rosa_mobile_returned",
            RosaKit.LAPTOP.value: "rosa_laptop_returned",
            RosaKit.KEY.value: "rosa_key_returned",
        }
        for rosa_key, task_log_field_name in rosa_values_mapping.items():
            rosa_kit = RosaKit(rosa_key)
            task_log: Optional[TaskLog] = getattr(
                self.leaving_request, task_log_field_name
            )

            if rosa_key in user_returned:
                if not task_log:
                    setattr(
                        self.leaving_request,
                        task_log_field_name,
                        (
                            self.leaving_request.task_logs.create(
                                user=user,
                                task_name=f"{rosa_kit.label} 'returned' checked",
                                notes=f"{rosa_kit.label} 'returned' checked",
                                reference=f"LeavingRequest.{task_log_field_name}",
                            )
                        ),
                    )
            else:
                if task_log:
                    self.leaving_request.task_logs.create(
                        user=user,
                        task_name=f"{rosa_kit.label} 'returned' unchecked",
                        notes=f"{rosa_kit.label} 'returned' unchecked",
                        reference=f"LeavingRequest.{task_log_field_name}",
                    )
                setattr(
                    self.leaving_request,
                    task_log_field_name,
                    None,
                )

        self.leaving_request.save()

        return super().form_valid(form)


class RosaKitConfirmationCloseView(
    UserPassesTestMixin,
    FormView,
):
    template_name = "leaving/security_team/confirmation/rosa_kit_action.html"
    page_title: str = "Security Team offboarding: ROSA Kit confirmation"
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
    page_title: str = "Security Team offboarding summary"

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            page_title=self.page_title,
        )

        rosa_kit_statuses = get_rosa_kit_statuses(leaving_request=self.leaving_request)
        rosa_kit_tasks = []

        for rosa_kit_value, status in rosa_kit_statuses.items():
            rosa_kit = RosaKit(rosa_kit_value)
            rosa_kit_tasks.append(
                {
                    "name": f"Retrieve {rosa_kit.label}",
                    "status": status,
                }
            )

        context.update(
            leaver_name=self.leaving_request.get_leaver_name(),
            leaving_request_uuid=self.leaving_request.uuid,
            pass_disabled=self.leaving_request.security_pass_disabled,
            pass_returned=self.leaving_request.security_pass_returned,
            pass_destroyed=self.leaving_request.security_pass_destroyed,
            pass_not_returned=self.leaving_request.security_pass_not_returned,
            rosa_kit_tasks=rosa_kit_tasks,
            rosa_kit_complete=bool(
                self.leaving_request.security_team_rosa_kit_complete
            ),
        )

        return context
