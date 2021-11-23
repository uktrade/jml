from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)

from leavers.forms import SREConfirmCompleteForm
from leavers.models import LeavingRequest, TaskLog

from core.utils.sre_messages import (
    send_sre_complete_message,
)


class TaskConfirmationView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    FormView,
):
    template_name = "leaving/task_form.html"
    form_class = SREConfirmCompleteForm
    success_url = reverse_lazy("sre-thank-you")
    leaving_request = None

    def test_func(self):
        return self.request.user.groups.filter(
            name="SRE",
        ).first()

    def form_valid(self, form):
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )

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
                setattr(self.leaving_request, value[0], TaskLog.objects.create(
                    user=self.request.user,
                    task_name=value[1],
                ))

        first_slack_message = self.leaving_request.slack_messages.order_by(
            "-created_at"
        ).first()

        # TODO handle None in above result
        send_sre_complete_message(
            thread_ts=first_slack_message.slack_timestamp,
        )

        return super(TaskConfirmationView, self).form_valid(form)


class ThankYouView(TemplateView):
    template_name = "leaving/sre_thank_you.html"
