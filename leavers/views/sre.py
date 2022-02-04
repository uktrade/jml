from django.contrib.auth.mixins import UserPassesTestMixin
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from core.utils.sre_messages import send_sre_complete_message
from leavers.forms import sre as sre_forms
from leavers.models import LeavingRequest, TaskLog


class TaskConfirmationView(
    UserPassesTestMixin,
    FormView,
):
    template_name = "leaving/task_form.html"
    form_class = sre_forms.SREConfirmCompleteForm
    leaving_request = None

    def test_func(self):
        return self.request.user.groups.filter(
            name="SRE",
        ).first()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        assert self.leaving_request
        return reverse_lazy("sre-thank-you", args=[self.leaving_request.uuid])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leaver_first_name = self.leaving_request.leaver_first_name
        leaver_last_name = self.leaving_request.leaver_last_name
        context["leaver_name"] = f"{leaver_first_name} {leaver_last_name}"
        context["leaving_date"] = self.leaving_request.last_day
        return context

    def form_valid(self, form):
        actions = {
            "vpn": ["vpn_access_removed", "VPN access removed"],
            "govuk_paas": ["govuk_paas_access_removed", "GOV.UK PAAS access removed"],
            "github": ["github_user_access_removed", "Github access removed"],
            "sentry": ["sentry_access_removed", "Sentry access removed"],
            "slack": ["slack_removed", "Slack access removed"],
            "sso": ["sso_access_removed", "SSO access removed"],
            "aws": ["aws_access_removed", "AWS access removed"],
            "jira": ["jira_access_removed", "Jira access removed"],
        }

        for key, value in actions.items():
            if form.cleaned_data[key]:
                setattr(
                    self.leaving_request,
                    value[0],
                    TaskLog.objects.create(
                        user=self.request.user,
                        task_name=value[1],
                    ),
                )

        first_slack_message = self.leaving_request.slack_messages.order_by(
            "-created_at"
        ).first()

        # TODO handle None in above result
        send_sre_complete_message(
            thread_ts=first_slack_message.slack_timestamp,
            leaving_request=self.leaving_request,
        )

        return super(TaskConfirmationView, self).form_valid(form)


class ThankYouView(UserPassesTestMixin, TemplateView):
    template_name = "leaving/sre_thank_you.html"

    def test_func(self):
        return self.request.user.groups.filter(
            name="SRE",
        ).first()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leaver_first_name = self.leaving_request.leaver_first_name
        leaver_last_name = self.leaving_request.leaver_last_name
        context.update(leaver_name=f"{leaver_first_name} {leaver_last_name}")
        return context
