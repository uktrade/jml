from datetime import timedelta
from typing import Any, Dict, List, Optional

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.postgres.search import SearchVector
from django.core.paginator import Paginator
from django.db.models.query import QuerySet
from django.http.response import HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic.edit import FormView

from leavers.forms import data_processor as data_processor_forms
from leavers.forms.leaver import SecurityClearance
from leavers.models import LeavingRequest


class LeavingRequestListing(
    UserPassesTestMixin,
    FormView,
):
    form_class = data_processor_forms.LeavingRequestListingSearchForm

    complete_field: str = ""
    query: str = ""
    show_complete: bool = False
    show_incomplete: bool = False
    confirmation_view: str = ""
    summary_view: str = ""
    service_name: Optional[str] = None
    fields: List[str] = [
        "leaver_name",
        "security_clearance",
        "work_email",
        "leaving_date",
        "last_working_day",
        "days_until_last_working_day",
        "reported_on",
        "complete",
    ]

    def __init__(
        self,
        show_complete: bool = False,
        show_incomplete: bool = False,
    ) -> None:
        super().__init__()
        self.show_complete = show_complete
        self.show_incomplete = show_incomplete

    def get_leaving_requests(self) -> QuerySet[LeavingRequest]:
        leaving_requests: QuerySet[LeavingRequest] = LeavingRequest.objects.all()
        complete_field = self.get_complete_field()
        if complete_field:
            if not self.show_complete:
                leaving_requests = leaving_requests.exclude(
                    **{self.get_complete_field() + "__isnull": False}
                )
            if not self.show_incomplete:
                leaving_requests = leaving_requests.exclude(
                    **{self.get_complete_field() + "__isnull": True}
                )

        # Search
        if self.query:
            leaving_requests = leaving_requests.annotate(
                search=SearchVector(
                    "leaver_information__leaver_first_name",
                    "leaver_information__leaver_last_name",
                    "leaver_activitystream_user__first_name",
                    "leaver_activitystream_user__last_name",
                    "leaver_activitystream_user__contact_email_address",
                )
            )
            leaving_requests = leaving_requests.filter(search=self.query)

        # Return filtered and searched leaving requests
        return leaving_requests

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            service_name=self.get_service_name(),
            show_complete=self.show_complete,
            show_incomplete=self.show_incomplete,
            fields=self.fields,
        )

        # Set object type name
        object_type_name = self.get_object_type_name()
        context.update(
            object_type_name=object_type_name,
            page_title=self.get_page_title(object_type_name),
        )

        # Build the results
        leaving_requests = self.get_leaving_requests()
        lr_results_data = []
        for lr in leaving_requests:
            complete_field = self.get_complete_field()
            is_complete: Optional[bool] = None
            if complete_field:
                is_complete = getattr(lr, self.get_complete_field())
            link = reverse_lazy(
                self.get_confirmation_view(), kwargs={"leaving_request_id": lr.uuid}
            )
            if is_complete:
                link = reverse_lazy(
                    self.get_summary_view(), kwargs={"leaving_request_id": lr.uuid}
                )

            lr_result_data = {
                "link": link,
                "leaver_name": lr.get_leaver_name(),
                "work_email": lr.get_leaver_email(),
                "complete": is_complete,
                "security_clearance": "Not yet known",
                "leaving_date": "Not yet known",
                "last_day": "Not yet known",
                "days_until_last_working_day": "Not yet known",
                "reported_on": "Not yet reported",
            }

            if lr.security_clearance:
                lr_result_data.update(
                    security_clearance=SecurityClearance(lr.security_clearance).label
                )

            if lr.line_manager_complete:
                lr_result_data.update(reported_on=lr.line_manager_complete.date())

            leaving_date = lr.get_leaving_date()
            last_day = lr.get_last_day()

            if leaving_date:
                lr_result_data.update(
                    leaving_date=leaving_date.date(),
                )
            if last_day:
                days_until_last_working_day: timedelta = (
                    last_day.date() - timezone.now().date()
                )

                lr_result_data.update(
                    last_working_day=last_day.date(),
                    days_until_last_working_day=days_until_last_working_day.days,
                )

            lr_results_data.append(lr_result_data)

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

    def get_page_title(self, object_type_name: str) -> str:
        return object_type_name.title()

    def get_object_type_name(self) -> str:
        object_type_name: str = "leaving requests"
        if self.show_complete and not self.show_incomplete:
            object_type_name = "complete leaving requests"
        if self.show_incomplete and not self.show_complete:
            object_type_name = "outstanding leaving requests"
        return object_type_name

    def get_service_name(self) -> Optional[str]:
        return self.service_name

    def get_summary_view(self) -> str:
        return self.summary_view

    def get_confirmation_view(self) -> str:
        return self.confirmation_view

    def get_complete_field(self) -> str:
        return self.complete_field

    def form_valid(self, form: Any) -> HttpResponse:
        self.query = form.cleaned_data["query"]
        return self.render_to_response(self.get_context_data(form=form))
