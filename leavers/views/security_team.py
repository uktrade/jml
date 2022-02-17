from django.contrib.auth.mixins import UserPassesTestMixin
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from leavers.forms import security_team as security_team_form
from leavers.models import LeavingRequest, TaskLog


class TaskConfirmationView(
    UserPassesTestMixin,
    FormView,
):
    template_name = "leaving/security_team/task_form.html"
    form_class = security_team_form.SecurityTeamConfirmCompleteForm
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
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        assert self.leaving_request
        return reverse_lazy("security-team-thank-you", args=[self.leaving_request.uuid])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leaver_first_name = self.leaving_request.leaver_first_name
        leaver_last_name = self.leaving_request.leaver_last_name
        context["leaver_name"] = f"{leaver_first_name} {leaver_last_name}"
        context["leaving_date"] = self.leaving_request.last_day
        return context

    def form_valid(self, form):
        actions = {
            "building_pass_access_revoked": [
                "building_pass_access_revoked",
                "Building access removed",
            ],
            "rosa_access_revoked": [
                "rosa_access_revoked",
                "ROSA access removed",
            ],
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

        return super(TaskConfirmationView, self).form_valid(form)


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

        context.update(leaver_name=self.leaving_request.get_leaver_name())

        return context
