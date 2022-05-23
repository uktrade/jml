from typing import Any, Dict, List, Literal, Tuple

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from core.utils.sre_messages import send_sre_complete_message
from leavers.forms import sre as sre_forms
from leavers.models import LeavingRequest, TaskLog
from leavers.views import base


class LeavingRequestListing(base.LeavingRequestListing):
    template_name = "leaving/sre/listing.html"

    complete_field = "sre_complete"
    confirmation_view = "sre-confirmation"
    summary_view = "sre-summary"
    page_title = "SRE access removal"
    service_name = "Leaving DIT: SRE actions"

    def test_func(self):
        return self.request.user.groups.filter(
            name="SRE",
        ).exists()


class TaskConfirmationView(base.TaskConfirmationView):
    template_name = "leaving/sre/task_form.html"
    form_class = sre_forms.SREConfirmCompleteForm
    complete_field = "sre_complete"
    page_title = "SRE access removal confirmation"

    # Field mapping from the Form field name to the LeavingRequest field name (with task messages)
    field_mapping: Dict[str, Tuple[str, str, str]] = {
        "vpn": (
            "vpn_access_removed",
            "VPN access removal confirmed",
            "VPN access removal unconfirmed",
        ),
        "govuk_paas": (
            "govuk_paas_access_removed",
            "GOV.UK PAAS access removal confirmed",
            "GOV.UK PAAS access removal unconfirmed",
        ),
        "github": (
            "github_user_access_removed",
            "Github access removal confirmed",
            "Github access removal unconfirmed",
        ),
        "sentry": (
            "sentry_access_removed",
            "Sentry access removal confirmed",
            "Sentry access removal unconfirmed",
        ),
        "slack": (
            "slack_removed",
            "Slack access removal confirmed",
            "Slack access removal unconfirmed",
        ),
        "sso": (
            "sso_access_removed",
            "SSO access removal confirmed",
            "SSO access removal unconfirmed",
        ),
        "aws": (
            "aws_access_removed",
            "AWS access removal confirmed",
            "AWS access removal unconfirmed",
        ),
        "jira": (
            "jira_access_removed",
            "Jira access removal confirmed",
            "Jira access removal unconfirmed",
        ),
    }

    def test_func(self):
        return self.request.user.groups.filter(
            name="SRE",
        ).exists()

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(
            completed=getattr(self.leaving_request, self.complete_field),
        )
        return form_kwargs

    def get_success_url(self) -> str:
        assert self.leaving_request
        return reverse_lazy("sre-thank-you", args=[self.leaving_request.uuid])

    def form_valid(self, form):
        response = super().form_valid(form)

        submission_type: Literal["save", "submit"] = "save"
        if "submit" in form.data:
            submission_type = "submit"

        if submission_type == "submit":
            first_slack_message = self.leaving_request.slack_messages.order_by(
                "-created_at"
            ).first()

            if not first_slack_message:
                raise Exception("No Slack messages found")

            # TODO handle None in above result
            send_sre_complete_message(
                thread_ts=first_slack_message.slack_timestamp,
                leaving_request=self.leaving_request,
            )

        return response


class TaskSummaryView(
    UserPassesTestMixin,
    TemplateView,
):
    template_name = "leaving/sre/summary.html"
    leaving_request = None
    page_title: str = "SRE access removal summary"

    def test_func(self):
        return self.request.user.groups.filter(
            name="SRE",
        ).exists()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        return super().dispatch(request, *args, **kwargs)

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
            if sre_service[2]
        ]
        context.update(
            leaver_name=self.leaving_request.get_leaver_name(),
            leaving_request_uuid=self.leaving_request.uuid,
            access_removed_services=access_removed_services,
        )

        return context


class ThankYouView(UserPassesTestMixin, TemplateView):
    template_name = "leaving/sre/thank_you.html"
    page_title: str = "SRE access removal thank you"

    def test_func(self):
        return self.request.user.groups.filter(
            name="SRE",
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
            leaving_request=self.leaving_request,
            access_removed_services=[
                sre_service[1]
                for sre_service in self.leaving_request.sre_services()
                if sre_service[2]
            ],
            complete=bool(self.leaving_request.sre_complete),
        )

        return context
