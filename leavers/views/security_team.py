from typing import Any, Dict, List, Tuple

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
from leavers.views import base


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
