from datetime import date
from typing import Any, Dict, List, Literal, Optional, Tuple, Type, cast

from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models.query import QuerySet
from django.forms import Form
from django.http import Http404
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic.edit import FormView

from core.utils.helpers import make_possessive
from core.views import BaseTemplateView
from leavers.forms.security_team import (
    AddTaskNoteForm,
    BuildingPassCloseRecordForm,
    BuildingPassForm,
    BuildingPassStatus,
    BuildingPassSteps,
    ClearanceStatus,
    RosaKit,
    RosaKitActions,
    RosaKitCloseRecordForm,
    RosaKitFieldForm,
    SecurityClearanceForm,
)
from leavers.models import LeavingRequest, TaskLog
from leavers.types import SecurityClearance
from leavers.utils.security_team import (
    SecuritySubRole,
    get_security_role,
    set_security_role,
)
from leavers.views import base
from leavers.views.leaver import LeavingRequestViewMixin
from leavers.views.sre import ServiceInfo
from user.models import User

ROSA_KIT: List[str] = [
    RosaKit.MOBILE.value,
    RosaKit.LAPTOP.value,
    RosaKit.KEY.value,
]
ROSA_KIT_FIELD_MAPPING: Dict[str, str] = {
    RosaKit.MOBILE.value: "rosa_mobile_returned",
    RosaKit.LAPTOP.value: "rosa_laptop_returned",
    RosaKit.KEY.value: "rosa_key_returned",
}


class IsSecurityTeamUser(UserPassesTestMixin):
    # TODO: Switch to a permission check
    def test_func(self):
        return self.request.user.groups.filter(
            name="Security Team",
        ).exists()


class SecurityViewMixin(IsSecurityTeamUser, LeavingRequestViewMixin, BaseTemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()

        manager_as_user = self.leaving_request.get_line_manager()
        assert manager_as_user

        leaving_datetime = self.leaving_request.get_leaving_date()
        leaving_date: Optional[date] = None
        if leaving_datetime:
            leaving_date = leaving_datetime.date()

        last_day_datetime = self.leaving_request.get_last_day()
        last_day: Optional[date] = None
        if last_day_datetime:
            last_day = last_day_datetime.date()

        leaver_security_clearance = self.leaving_request.get_security_clearance()
        assert leaver_security_clearance

        context.update(
            leaver_name=leaver_name,
            leaver_email=self.leaving_request.get_leaver_email(),
            leaver_security_clearance=leaver_security_clearance.label,
            manager_name=manager_as_user.full_name,
            manager_emails=manager_as_user.get_email_addresses_for_contact(),
            leaving_date=leaving_date,
            last_working_day=last_day,
            complete=bool(self.leaving_request.security_team_building_pass_complete),
        )
        return context


class LeavingRequestListing(IsSecurityTeamUser, base.LeavingRequestListing):
    template_name = "leaving/security_team/listing.html"

    fields: List[Tuple[str, str]] = [
        ("leaver_name", "Leaver's name"),
        ("security_clearance", "Security Clearance level"),
        ("work_email", "Email"),
        ("leaving_date", "Leaving date"),
        ("last_working_day", "Last working day"),
        ("days_until_last_working_day", "Days left"),
        ("complete", "Status"),
    ]

    building_pass_confirmation_view = "security-team-building-pass-confirmation"
    rosa_kit_confirmation_view = "security-team-rosa-kit-confirmation"
    summary_view = "security-team-summary"

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
        leaving_requests = leaving_requests.exclude(line_manager_complete__isnull=True)

        if self.role == SecuritySubRole.ROSA_KIT:
            leaving_requests = leaving_requests.filter(is_rosa_user=True)

        return leaving_requests

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        self.role = get_security_role(request)
        return super().dispatch(request, *args, **kwargs)

    def get_page_title(self, object_type_name: str) -> str:
        if self.role == SecuritySubRole.BUILDING_PASS:
            return "Security requests"
        elif self.role == SecuritySubRole.ROSA_KIT:
            return "ROSA Kit requests"
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

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(security_role=self.role)
        return context


class BuildingPassConfirmationView(
    SecurityViewMixin,
    FormView,
):
    template_name = "leaving/security_team/confirmation/building_pass.html"
    form_class = AddTaskNoteForm
    success_viewname = "security-team-building-pass-confirmation"
    back_link_url = reverse_lazy("security-team-listing-incomplete")

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        set_security_role(request=request, role=SecuritySubRole.BUILDING_PASS)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leaver_name = self.leaving_request.get_leaver_name()
        context.update(page_title=f"{leaver_name} building pass")

        security_clearance_can_complete: bool = False
        security_clearance_status: Optional[ClearanceStatus] = None
        security_clearance_other_label: Optional[str] = None
        if self.leaving_request.security_clearance_status:
            security_clearance_status = ClearanceStatus(
                self.leaving_request.security_clearance_status.value
            )
            if security_clearance_status == ClearanceStatus.OTHER:
                security_clearance_other_label = (
                    self.leaving_request.security_clearance_status.notes
                )
            if security_clearance_status in [
                ClearanceStatus.LAPSED,
                ClearanceStatus.OTHER,
            ]:
                security_clearance_can_complete = True

        context.update(
            leaving_request_uuid=self.leaving_request.uuid,
            pass_disabled=self.leaving_request.security_pass_disabled,
            pass_returned=self.leaving_request.security_pass_returned,
            pass_destroyed=self.leaving_request.security_pass_destroyed,
            security_clearance_status_task_log=self.leaving_request.security_clearance_status,
            security_clearance_status=security_clearance_status,
            security_clearance_other_label=security_clearance_other_label,
            can_complete=all(
                [
                    self.leaving_request.security_pass_disabled,
                    self.leaving_request.security_pass_returned,
                    self.leaving_request.security_pass_destroyed,
                    security_clearance_can_complete,
                ]
            ),
            task_notes=self.leaving_request.get_security_building_pass_notes(),
        )

        return context

    def form_valid(self, form) -> HttpResponse:
        note = form.cleaned_data["note"]

        user = cast(User, self.request.user)

        self.leaving_request.task_logs.create(
            user=user,
            task_name="A comment has been added.",
            notes=note,
            reference="LeavingRequest.security_team_building_pass_complete",
        )
        return super().form_valid(form)


class BuildingPassConfirmationEditView(SecurityViewMixin, FormView):
    template_name = "leaving/security_team/confirmation/building_pass_edit.html"
    form_class = BuildingPassForm
    success_viewname = "security-team-building-pass-confirmation"
    back_link_url = reverse_lazy("security-team-listing-incomplete")
    back_link_text = "Back to Building pass requests"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        set_security_role(request=request, role=SecuritySubRole.BUILDING_PASS)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leaver_name = self.leaving_request.get_leaver_name()
        context.update(
            leaving_request_uuid=self.leaving_request.uuid,
            page_title=f"{leaver_name} building pass",
            pass_disabled=self.leaving_request.security_pass_disabled,
            pass_returned=self.leaving_request.security_pass_returned,
            pass_destroyed=self.leaving_request.security_pass_destroyed,
            complete=bool(self.leaving_request.security_team_building_pass_complete),
        )

        return context

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(leaving_request_uuid=self.leaving_request.uuid)
        return form_kwargs

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()

        initial["pass_status"] = BuildingPassStatus.ACTIVE.value
        if self.leaving_request.security_pass_disabled:
            initial["pass_status"] = BuildingPassStatus.DEACTIVATED.value

        initial["next_steps"] = []
        if self.leaving_request.security_pass_returned:
            initial["next_steps"].append(BuildingPassSteps.RETURNED.value)
        if self.leaving_request.security_pass_destroyed:
            initial["next_steps"].append(BuildingPassSteps.DESTROYED.value)

        return initial

    def form_valid(self, form):
        user = cast(User, self.request.user)

        # Mark the pass as being deactivated.
        if (
            form.cleaned_data["pass_status"] == BuildingPassStatus.DEACTIVATED
            and not self.leaving_request.security_pass_disabled
        ):
            self.leaving_request.security_pass_disabled = (
                self.leaving_request.task_logs.create(
                    user=user,
                    task_name="Building pass marked as deactivated",
                    reference="LeavingRequest.security_pass_disabled",
                )
            )
        # Unmark the pass as being deactivated.
        if (
            form.cleaned_data["pass_status"] == BuildingPassStatus.ACTIVE
            and self.leaving_request.security_pass_disabled
        ):
            self.leaving_request.security_pass_disabled = None
            self.leaving_request.task_logs.create(
                user=user,
                task_name="Building pass marked as activated",
                reference="LeavingRequest.security_pass_disabled",
            )

        # Mark the pass as returned.
        if (
            BuildingPassSteps.RETURNED.value in form.cleaned_data["next_steps"]
            and not self.leaving_request.security_pass_returned
        ):
            self.leaving_request.security_pass_returned = (
                self.leaving_request.task_logs.create(
                    user=user,
                    task_name="Building pass 'returned' checked",
                    reference="LeavingRequest.security_pass_returned",
                )
            )
        # Unmark the pass as returned.
        if (
            BuildingPassSteps.RETURNED.value not in form.cleaned_data["next_steps"]
            and self.leaving_request.security_pass_returned
        ):
            self.leaving_request.security_pass_returned = None
            self.leaving_request.task_logs.create(
                user=user,
                task_name="Building pass 'returned' unchecked",
                reference="LeavingRequest.security_pass_returned",
            )

        # Mark the pass as destroyed.
        if (
            BuildingPassSteps.DESTROYED.value in form.cleaned_data["next_steps"]
            and not self.leaving_request.security_pass_destroyed
        ):
            self.leaving_request.security_pass_destroyed = (
                self.leaving_request.task_logs.create(
                    user=user,
                    task_name="Building pass 'destroyed' checked",
                    reference="LeavingRequest.security_pass_destroyed",
                )
            )
        # Unmark the pass as returned.
        if (
            BuildingPassSteps.DESTROYED.value not in form.cleaned_data["next_steps"]
            and self.leaving_request.security_pass_destroyed
        ):
            self.leaving_request.security_pass_destroyed = None
            self.leaving_request.task_logs.create(
                user=user,
                task_name="Building pass 'destroyed' unchecked",
                reference="LeavingRequest.security_pass_destroyed",
            )

        self.leaving_request.save()

        return super().form_valid(form)


class BuidlingPassConfirmationCloseView(SecurityViewMixin, FormView):
    template_name = "leaving/security_team/confirmation/building_pass_action.html"
    form_class = BuildingPassCloseRecordForm
    success_viewname = "security-team-summary"
    back_link_viewname = "security-team-building-pass-confirmation"
    back_link_text = "Back to Building pass requests"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        response = super().dispatch(request, *args, **kwargs)
        if self.leaving_request.security_team_rosa_kit_complete:
            return redirect(self.get_success_url())
        return response

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(leaving_request_uuid=self.leaving_request.uuid)

        return form_kwargs

    def form_valid(self, form):
        self.leaving_request.security_team_building_pass_complete = timezone.now()
        self.leaving_request.save()
        return super().form_valid(form)

    def get_page_title(self):
        possessive_leaver_name = make_possessive(self.leaving_request.get_leaver_name())

        return f"{possessive_leaver_name} Building pass: confirm record is complete"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            leaving_request=self.leaving_request,
            leaving_request_uuid=self.leaving_request.uuid,
            page_title=self.get_page_title(),
        )
        return context


class SecurityClearanceConfirmationEditView(SecurityViewMixin, FormView):
    template_name = "leaving/security_team/confirmation/building_pass_edit.html"
    form_class = SecurityClearanceForm
    back_link_url = reverse_lazy("security-team-listing-incomplete")
    back_link_text = "Back to Building pass requests"

    def get_success_url(self) -> str:
        return reverse_lazy(
            "security-team-building-pass-confirmation", args=[self.leaving_request.uuid]
        )

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        set_security_role(request=request, role=SecuritySubRole.BUILDING_PASS)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name = make_possessive(leaver_name)
        context.update(page_title=f"{possessive_leaver_name} security clearance")

        security_clearance_status: Optional[ClearanceStatus] = None
        if self.leaving_request.security_clearance_status:
            security_clearance_status = ClearanceStatus(
                self.leaving_request.security_clearance_status.value
            )

        context.update(
            leaving_request_uuid=self.leaving_request.uuid,
            security_clearance_status=security_clearance_status,
            complete=bool(self.leaving_request.security_team_building_pass_complete),
        )

        return context

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(leaving_request_uuid=self.leaving_request.uuid)
        return form_kwargs

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()

        clearance_level: SecurityClearance = SecurityClearance(
            self.leaving_request.security_clearance
        )

        if self.leaving_request.security_clearance_level:
            clearance_level = SecurityClearance(
                self.leaving_request.security_clearance_level.value
            )

        security_clearance_status: ClearanceStatus = ClearanceStatus.ACTIVE
        security_clearance_other_value: Optional[str] = None

        if self.leaving_request.security_clearance_status:
            security_clearance_status = ClearanceStatus(
                self.leaving_request.security_clearance_status.value
            )
            if security_clearance_status == ClearanceStatus.OTHER:
                security_clearance_other_value = (
                    self.leaving_request.security_clearance_status.notes
                )

        initial["clearance_level"] = clearance_level.value
        initial["status"] = security_clearance_status.value
        initial["other_value"] = security_clearance_other_value

        return initial

    def form_valid(self, form):
        user = cast(User, self.request.user)

        clearance_level: Optional[SecurityClearance] = None
        if self.leaving_request.security_clearance_level:
            clearance_level = SecurityClearance(
                self.leaving_request.security_clearance_level.value
            )

        form_clearance_level = form.cleaned_data["clearance_level"]

        if clearance_level != form_clearance_level:
            self.leaving_request.security_clearance_level = (
                self.leaving_request.task_logs.create(
                    user=user,
                    task_name=(
                        f"Security clearance level changed to {clearance_level}"
                    ),
                    reference="LeavingRequest.security_clearance_level",
                    value=form_clearance_level,
                )
            )

        security_clearance_status: Optional[ClearanceStatus] = None
        security_clearance_other_value: Optional[str] = None
        if self.leaving_request.security_clearance_status:
            security_clearance_status = ClearanceStatus(
                self.leaving_request.security_clearance_status.value
            )
            if security_clearance_status == ClearanceStatus.OTHER:
                security_clearance_other_value = (
                    self.leaving_request.security_clearance_status.notes
                )

        status = form.cleaned_data["status"]
        other_value = form.cleaned_data["other_value"]

        status_changed: bool = False
        if security_clearance_status != status:
            status_changed = True
        elif (
            status == ClearanceStatus.OTHER.value
            and security_clearance_other_value != other_value
        ):
            status_changed = True

        if status_changed:
            self.leaving_request.security_clearance_status = (
                self.leaving_request.task_logs.create(
                    user=user,
                    task_name=(
                        "Security clearance status changed from "
                        f"{security_clearance_status} to {status}"
                    ),
                    reference="LeavingRequest.security_clearance_status",
                    value=status,
                    notes=other_value,
                )
            )

        self.leaving_request.save(
            update_fields=[
                "security_clearance_level",
                "security_clearance_status",
            ]
        )

        return super().form_valid(form)


def get_rosa_kit_statuses(leaving_request: LeavingRequest) -> Dict[str, Dict[str, str]]:
    if not leaving_request.is_rosa_user:
        return {}

    rosa_kit_statuses: Dict[Any, Dict[str, str]] = {
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

    for rk in ROSA_KIT:
        rosa_kit_field = ROSA_KIT_FIELD_MAPPING[rk]
        rosa_task_log: Optional[TaskLog] = getattr(leaving_request, rosa_kit_field)
        if rosa_task_log:
            if rosa_task_log.value == RosaKitActions.NOT_STARTED:
                rosa_kit_statuses[rk]["colour"] = "grey"
                rosa_kit_statuses[rk]["text"] = "Not started"
            elif rosa_task_log.value == RosaKitActions.NOT_APPLICABLE:
                rosa_kit_statuses[rk]["colour"] = "grey"
                rosa_kit_statuses[rk]["text"] = "N/A"
            elif rosa_task_log.value == RosaKitActions.RETURNED:
                rosa_kit_statuses[rk]["colour"] = "green"
                rosa_kit_statuses[rk]["text"] = "Returned"

    return rosa_kit_statuses


class RosaKitConfirmationView(SecurityViewMixin):
    template_name = "leaving/security_team/confirmation/rosa_kit.html"
    success_viewname = "security-team-rosa-kit-confirmation"
    back_link_url = reverse_lazy("security-team-listing-incomplete")

    def get_page_title(self) -> str:
        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name: str = ""
        if leaver_name:
            possessive_leaver_name = make_possessive(leaver_name)
        return f"{possessive_leaver_name} ROSA Kit"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        set_security_role(request=request, role=SecuritySubRole.ROSA_KIT)
        return super().dispatch(request, *args, **kwargs)

    def get_kit_info(self) -> List[ServiceInfo]:
        kit_info: List[ServiceInfo] = []
        for kit_item in ROSA_KIT:
            rosa_kit = RosaKit(kit_item)
            rosa_kit_field = ROSA_KIT_FIELD_MAPPING[kit_item]

            rosa_info = ServiceInfo(
                field_name=rosa_kit_field,
                name=rosa_kit.label,
                comment="",
                status_colour="grey",
                status_text="Not started",
            )

            # Get the action stored against the field
            rosa_task_log: Optional[TaskLog] = getattr(
                self.leaving_request, rosa_kit_field
            )

            if rosa_task_log:
                if rosa_task_log.value == RosaKitActions.NOT_STARTED:
                    rosa_info["status_colour"] = "grey"
                    rosa_info["status_text"] = "Not started"
                elif rosa_task_log.value == RosaKitActions.NOT_APPLICABLE:
                    rosa_info["status_colour"] = "grey"
                    rosa_info["status_text"] = "N/A"
                elif rosa_task_log.value == RosaKitActions.RETURNED:
                    rosa_info["status_colour"] = "green"
                    rosa_info["status_text"] = "Returned"

            # Get the most recent note referring to this field.
            most_recent_rosa_task_log: Optional[TaskLog] = (
                self.leaving_request.task_logs.filter(
                    reference=f"LeavingRequest.{rosa_kit_field}"
                )
                .order_by("-created_at")
                .first()
            )
            if most_recent_rosa_task_log:
                rosa_info["comment"] = most_recent_rosa_task_log.notes or ""

            kit_info.append(rosa_info)

        return kit_info

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            page_title=self.get_page_title(),
            leaving_request_uuid=self.leaving_request.uuid,
            kit_info=self.get_kit_info(),
        )

        can_mark_as_complete: bool = True
        for rk in ROSA_KIT:
            rosa_kit_field_name = ROSA_KIT_FIELD_MAPPING[rk]
            rosa_kit_task_log: Optional[TaskLog] = getattr(
                self.leaving_request, rosa_kit_field_name
            )
            if not rosa_kit_task_log:
                can_mark_as_complete = False
                break
            elif rosa_kit_task_log and rosa_kit_task_log.value not in [
                RosaKitActions.NOT_APPLICABLE,
                RosaKitActions.RETURNED,
            ]:
                can_mark_as_complete = False
                break

        context.update(can_mark_as_complete=can_mark_as_complete)

        return context


class RosaKitFieldView(SecurityViewMixin):
    template_name = "leaving/security_team/confirmation/rosa_kit_edit.html"
    forms: Dict[str, Type[Form]] = {
        "update_status_form": RosaKitFieldForm,
        "add_note_form": AddTaskNoteForm,
    }
    success_viewname = "security-team-rosa-kit-confirmation"
    back_link_viewname = "security-team-rosa-kit-confirmation"
    back_link_text = "Back to ROSA Kit requests"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        self.field_name = self.kwargs.get("field_name", None)
        if not self.field_name:
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get_page_title(self) -> str:
        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name: str = ""
        if leaver_name:
            possessive_leaver_name = make_possessive(leaver_name)
        return f"{possessive_leaver_name} ROSA Kit"

    def post_update_status_form(
        self, request: HttpRequest, form: Form, *args, **kwargs
    ):
        user = cast(User, request.user)

        action_value = form.cleaned_data["action"]
        action = RosaKitActions(action_value)

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

        user = cast(User, self.request.user)

        self.leaving_request.task_logs.create(
            user=user,
            task_name="A comment has been added.",
            notes=note,
            reference=f"LeavingRequest.{self.field_name}",
        )

        return redirect(
            self.get_view_url(
                "security-team-rosa-kit-field", field_name=self.field_name
            )
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

        context.update(page_title=self.get_page_title())

        rosa_kit = None
        for rk, field_name in ROSA_KIT_FIELD_MAPPING.items():
            if field_name == self.field_name:
                rosa_kit = RosaKit(rk)

        context.update(
            rosa_kit_name=rosa_kit.label,
            leaving_request_uuid=self.leaving_request.uuid,
            task_notes=self.leaving_request.get_security_rosa_kit_notes(
                field_name=self.field_name
            ),
        )

        return context


class RosaKitConfirmationCloseView(SecurityViewMixin, FormView):
    template_name = "leaving/security_team/confirmation/rosa_kit_action.html"
    form_class = RosaKitCloseRecordForm
    success_viewname = "security-team-summary"
    back_link_viewname = "security-team-rosa-kit-confirmation"
    back_link_text = "Back to ROSA Kit requests"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        response = super().dispatch(request, *args, **kwargs)
        if self.leaving_request.security_team_rosa_kit_complete:
            return redirect(self.get_success_url())
        return response

    def get_page_title(self) -> str:
        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name: str = ""
        if leaver_name:
            possessive_leaver_name = make_possessive(leaver_name)
        return f"{possessive_leaver_name} ROSA Kit: confirm record is complete"

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


class TaskSummaryView(SecurityViewMixin):
    template_name = "leaving/security_team/summary.html"
    back_link_url = reverse_lazy("security-team-listing-complete")

    def get_page_title(self) -> str:
        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name: str = ""
        if leaver_name:
            possessive_leaver_name = make_possessive(leaver_name)
        return f"{possessive_leaver_name} security offboarding summary"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            page_title=self.get_page_title(),
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

        security_clearance_status: Optional[ClearanceStatus] = None
        security_clearance_other_value: Optional[str] = None
        if self.leaving_request.security_clearance_status:
            security_clearance_status = ClearanceStatus(
                self.leaving_request.security_clearance_status.value
            )
            if security_clearance_status == ClearanceStatus.OTHER:
                security_clearance_other_value = (
                    self.leaving_request.security_clearance_status.notes
                )

        context.update(
            leaving_request_uuid=self.leaving_request.uuid,
            pass_disabled=self.leaving_request.security_pass_disabled,
            pass_returned=self.leaving_request.security_pass_returned,
            pass_destroyed=self.leaving_request.security_pass_destroyed,
            security_clearance_status=security_clearance_status,
            security_clearance_other_value=security_clearance_other_value,
            rosa_kit_tasks=rosa_kit_tasks,
            rosa_kit_complete=bool(
                self.leaving_request.security_team_rosa_kit_complete
            ),
        )

        return context
