from typing import Any, Dict, List, Literal, Tuple

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.postgres.search import SearchVector
from django.core.paginator import Paginator
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from core.utils.sre_messages import send_sre_complete_message
from leavers.forms import sre as sre_forms
from leavers.models import LeavingRequest, TaskLog
from leavers.views import base


class LeavingRequestListing(
    UserPassesTestMixin,
    FormView,
):
    template_name = "leaving/sre/listing.html"
    form_class = sre_forms.SRESearchForm

    query: str = ""
    show_complete: bool = False
    show_incomplete: bool = False

    def __init__(
        self,
        show_complete: bool = False,
        show_incomplete: bool = False,
    ) -> None:
        super().__init__()
        self.show_complete = show_complete
        self.show_incomplete = show_incomplete

    def test_func(self):
        return self.request.user.groups.filter(
            name="SRE",
        ).first()

    def get_leaving_requests(self) -> List[LeavingRequest]:
        # Filter
        leaving_requests = LeavingRequest.objects.all()
        if not self.show_complete:
            leaving_requests = leaving_requests.exclude(sre_complete__isnull=False)
        if not self.show_incomplete:
            leaving_requests = leaving_requests.exclude(sre_complete__isnull=True)

        # Search
        if self.query:
            leaving_requests = leaving_requests.annotate(
                search=SearchVector(
                    "leaver_information__leaver_first_name",
                    "leaver_information__leaver_last_name",
                    "leaver_activitystream_user__first_name",
                    "leaver_activitystream_user__last_name",
                    "leaver_activitystream_user__email_address",
                )
            )
            leaving_requests = leaving_requests.filter(search=self.query)

        # Return filtered and searched leaving requests
        return leaving_requests

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # Set object type name
        object_type_name: str = "leaving requests"
        if self.show_complete and not self.show_incomplete:
            object_type_name: str = "complete leaving requests"
        if self.show_incomplete and not self.show_complete:
            object_type_name: str = "incomplete leaving requests"
        context.update(object_type_name=object_type_name)

        # Build the results
        leaving_requests = self.get_leaving_requests()
        lr_results_data = []
        for lr in leaving_requests:
            link = reverse_lazy(
                "sre-confirmation", kwargs={"leaving_request_id": lr.uuid}
            )
            if lr.sre_complete:
                link = reverse_lazy(
                    "sre-summary", kwargs={"leaving_request_id": lr.uuid}
                )

            lr_results_data.append(
                {
                    "link": link,
                    "last_day": lr.last_day,
                    "leaver_name": lr.get_leaver_name(),
                    "leaver_email": lr.get_leaver_email(),
                    "complete": lr.sre_complete,
                }
            )

        # Paginate the results
        paginator = Paginator(lr_results_data, 20)
        page_number: int = int(self.request.GET.get("page", 1))
        page = paginator.page(page_number)

        pagination_pages: List[int] = []

        if page_number - 1 > 1:
            pagination_pages.append(page_number - 1)

        pagination_pages.append(page_number)

        if page_number + 1 < paginator.num_pages:
            pagination_pages.append(page_number + 1)

        context.update(page=page, pagination_pages=pagination_pages)

        return context

    def form_valid(self, form: Any) -> HttpResponse:
        self.query = form.cleaned_data["query"]
        return self.render_to_response(self.get_context_data(form=form))


class TaskConfirmationView(base.TaskConfirmationView):
    template_name = "leaving/sre/task_form.html"
    form_class = sre_forms.SREConfirmCompleteForm
    complete_field: str = "sre_complete"

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
        ).first()

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

    def test_func(self):
        return self.request.user.groups.filter(
            name="SRE",
        ).first()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        if not self.leaving_request.sre_complete:
            return redirect(
                reverse("sre-confirmation", args=[self.leaving_request.uuid])
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        access_removed_services: List[Tuple[str, str, TaskLog]] = {
            (
                sre_service[0],
                sre_service[1],
                getattr(self.leaving_request, sre_service[0]),
            )
            for sre_service in self.leaving_request.sre_services()
            if sre_service[2]
        }
        context.update(
            leaver_name=self.leaving_request.get_leaver_name(),
            access_removed_services=access_removed_services,
        )

        return context


class ThankYouView(UserPassesTestMixin, TemplateView):
    template_name = "leaving/sre/thank_you.html"

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

        context.update(
            leaver_name=self.leaving_request.get_leaver_name(),
            leaving_request=self.leaving_request,
            access_removed_services=[
                sre_service[1]
                for sre_service in self.leaving_request.sre_services()
                if sre_service[2]
            ],
        )

        return context
