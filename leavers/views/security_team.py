from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView

from leavers.models import LeavingRequest, TaskLog
from leavers.utils.leaving_request import get_email_task_logs
from leavers.views import base
from leavers.workflow.tasks import EmailIds


class SecuritySubRole(Enum):
    BUILDING_PASS = "bp"
    ROSA_KIT = "rk"


def get_security_role(request: HttpRequest) -> SecuritySubRole:
    """
    Get the security role from the URL or Session.

    If there is no role set yet, default to the Building Pass role.
    """
    role_value: Optional[str] = request.session.get("security_role", None)
    url_value: Optional[str] = request.GET.get("security-role")
    if url_value:
        role_value = url_value

    role: SecuritySubRole = SecuritySubRole.BUILDING_PASS
    if role_value:
        try:
            role = SecuritySubRole(role_value)
        except ValueError:
            pass

        request.session["security_role"] = role.value
        request.session.save()

    return role


class LeavingRequestListing(base.LeavingRequestListing):
    template_name = "leaving/security_team/listing.html"

    complete_field = "security_team_complete"
    building_pass_confirmation_view = "security-team-building-pass-confirmation"
    rosa_kit_confirmation_view = "security-team-rosa-kit-confirmation"
    summary_view = "security-team-summary"
    service_name = "Leaving DIT: Security actions"

    def test_func(self):
        return self.request.user.groups.filter(
            name="Security Team",
        ).exists()

    def get_confirmation_view(self) -> str:
        role = get_security_role(self.request)
        if role == SecuritySubRole.BUILDING_PASS:
            return self.building_pass_confirmation_view
        elif role == SecuritySubRole.ROSA_KIT:
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
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            page_title=self.page_title,
        )

        context.update(
            leaver_name=self.leaving_request.get_leaver_name(),
            leaver_email=self.leaving_request.get_leaver_email(),
            manager_name=self.leaving_request.get_line_manager_name(),
            manager_email=self.leaving_request.get_line_manager_email(),
            last_working_day=self.leaving_request.last_day.date(),
            leaving_date=self.leaving_request.leaving_date.date(),
            leaving_request_uuid=self.leaving_request.uuid,
            notifications=self.get_notifications(),
            can_mark_as_not_returned=bool(
                self.leaving_request.leaving_date < timezone.now()
            ),
        )

        return context

    def get_notifications(self) -> List[Dict[str, str]]:
        notifications = []

        # Reminder sent to Line manager
        # TODO: Update to be the right email_id
        line_manager_reminder_emails: List[TaskLog] = get_email_task_logs(
            leaving_request=self.leaving_request,
            email_id=EmailIds.LINE_MANAGER_REMINDER,
        )
        line_manager_last_sent: Optional[datetime] = None
        for line_manager_reminder_email in line_manager_reminder_emails:
            if (
                not line_manager_last_sent
                or line_manager_last_sent < line_manager_reminder_email.created_at
            ):
                line_manager_last_sent = line_manager_reminder_email.created_at

        notifications.append(
            {
                "sent": bool(line_manager_reminder_emails),
                "name": "Automated reminder sent to Line manager",
                "last_sent": line_manager_last_sent,
            }
        )

        # Reminder sent to Leaver
        # TODO: Update to be the right email_id
        leaver_reminder_emails: List[TaskLog] = get_email_task_logs(
            leaving_request=self.leaving_request,
            email_id=EmailIds.SECURITY_OFFBOARD_LEAVER_REMINDER,
        )
        leaver_last_sent: Optional[datetime] = None
        for leaver_reminder_email in leaver_reminder_emails:
            if (
                not leaver_last_sent
                or leaver_last_sent < leaver_reminder_email.created_at
            ):
                leaver_last_sent = leaver_reminder_email.created_at

        notifications.append(
            {
                "sent": bool(leaver_reminder_emails),
                "name": "Automated reminder sent to Leaver",
                "last_sent": leaver_last_sent,
            }
        )

        return notifications


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            page_title=self.page_title,
        )

        context.update(
            leaver_name=self.leaving_request.get_leaver_name(),
            leaving_request_uuid=self.leaving_request.uuid,
        )

        return context


class ThankYouView(UserPassesTestMixin, TemplateView):
    template_name = "leaving/security_team/thank_you.html"
    page_title: str = "Security Team off-boarding thank you"

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
            leaving_request_uuid=self.leaving_request.uuid,
            leaver_name=self.leaving_request.get_leaver_name(),
            line_manager_name=self.leaving_request.get_line_manager_name(),
            complete=bool(self.leaving_request.security_team_complete),
        )

        return context
