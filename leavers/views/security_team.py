from typing import Any, Dict, List, Tuple

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView

from leavers.forms import security_team as security_team_forms
from leavers.models import LeavingRequest, TaskLog
from leavers.views import base


class LeavingRequestListing(base.LeavingRequestListing):
    template_name = "leaving/security_team/listing.html"

    complete_field: str = "security_team_complete"
    confirmation_view: str = "security-team-confirmation"
    summary_view: str = "security-team-summary"

    def test_func(self):
        return self.request.user.groups.filter(
            name="Security Team",
        ).first()


class TaskConfirmationView(base.TaskConfirmationView):
    template_name = "leaving/security_team/task_form.html"
    form_class = security_team_forms.SecurityTeamConfirmCompleteForm
    complete_field: str = "security_team_complete"

    # Field mapping from the Form field name to the LeavingRequest field name (with task messages)
    field_mapping: Dict[str, Tuple[str, str, str]] = {
        "security_pass": (
            "security_pass",
            "Security pass {action} confirmed",
            "Security pass {action} uncomfirmed",
        ),
        "rosa_laptop_returned": (
            "rosa_laptop_returned",
            "ROSA laptop return confirmed",
            "ROSA laptop return uncomfirmed",
        ),
        "rosa_key_returned": [
            "rosa_key_returned",
            "ROSA key return confirmed",
            "ROSA key return unconfirmed",
        ],
    }

    def test_func(self):
        return self.request.user.groups.filter(
            name="Security Team",
        ).first()

    def get_success_url(self) -> str:
        assert self.leaving_request
        return reverse_lazy("security-team-thank-you", args=[self.leaving_request.uuid])

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()

        for key, value in self.field_mapping.items():
            leaving_request_value: TaskLog = getattr(self.leaving_request, value[0])
            if key == "security_pass":
                for security_pass_choice in security_team_forms.SecurityPassChoices:
                    if (
                        leaving_request_value
                        and security_pass_choice.value
                        in leaving_request_value.task_name
                    ):
                        initial[key] = security_pass_choice.value
                        break
            else:
                initial[key] = bool(leaving_request_value)

        return initial

    def format_task_name(self, field_key: str, task_name: str, field_value: Any) -> str:
        if field_key == "security_pass":
            return task_name.format(action=field_value)
        return super().format_task_name(
            field_key=field_key,
            task_name=task_name,
            field_value=field_value,
        )


class TaskSummaryView(
    UserPassesTestMixin,
    TemplateView,
):
    template_name = "leaving/security_team/summary.html"
    leaving_request = None

    def test_func(self):
        return self.request.user.groups.filter(
            name="Security Team",
        ).first()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        if not self.leaving_request.sre_complete:
            return redirect(
                reverse("security-team-confirmation", args=[self.leaving_request.uuid])
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        security_access_items: List[Tuple[str, str, TaskLog]] = [
            (
                security_access_item[0],
                security_access_item[1],
                getattr(self.leaving_request, security_access_item[0]),
            )
            for security_access_item in self.leaving_request.security_access()
            if security_access_item[2]
        ]
        context.update(
            leaver_name=self.leaving_request.get_leaver_name(),
            security_access_items=security_access_items,
        )

        return context


class ThankYouView(UserPassesTestMixin, TemplateView):
    template_name = "leaving/security_team/thank_you.html"

    def test_func(self):
        return self.request.user.groups.filter(
            name="Security Team",
        ).first()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            leaver_name=self.leaving_request.get_leaver_name(),
            line_manager_name=self.leaving_request.get_line_manager_name(),
            security_access=[
                security_item[1]
                for security_item in self.leaving_request.security_access()
                if security_item[2]
            ],
            complete=bool(self.leaving_request.security_team_complete),
        )

        return context
