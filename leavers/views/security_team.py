from typing import Any, Dict, List

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.postgres.search import SearchVector
from django.core.paginator import Paginator
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from leavers.forms import security_team as security_team_forms
from leavers.models import LeavingRequest, TaskLog


class LeavingRequestListing(
    UserPassesTestMixin,
    FormView,
):
    template_name = "leaving/security_team/listing.html"
    form_class = security_team_forms.SecurityTeamSearchForm

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
            name="Security Team",
        ).first()

    def get_leaving_requests(self) -> List[LeavingRequest]:
        # Filter
        leaving_requests = LeavingRequest.objects.all()
        if not self.show_complete:
            leaving_requests = leaving_requests.exclude(
                security_team_complete__isnull=False
            )
        if not self.show_incomplete:
            leaving_requests = leaving_requests.exclude(
                security_team_complete__isnull=True
            )

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
                "security-team-confirmation", kwargs={"leaving_request_id": lr.uuid}
            )
            if lr.security_team_complete:
                link = reverse_lazy(
                    "security-team-summary", kwargs={"leaving_request_id": lr.uuid}
                )

            lr_results_data.append(
                {
                    "link": link,
                    "last_day": lr.last_day,
                    "leaver_name": lr.get_leaver_name(),
                    "leaver_email": lr.get_leaver_email(),
                    "complete": lr.security_team_complete,
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


class TaskConfirmationView(
    UserPassesTestMixin,
    FormView,
):
    template_name = "leaving/security_team/task_form.html"
    form_class = security_team_forms.SecurityTeamConfirmCompleteForm
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
        context["leaver_name"] = self.leaving_request.get_leaver_name()
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
