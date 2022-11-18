from collections import OrderedDict
from datetime import timedelta
from typing import Any, Dict, List, Literal, Optional, Set, Tuple, cast

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.postgres.search import SearchVector
from django.core.paginator import Paginator
from django.db.models import Value
from django.db.models.functions import Concat
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.shortcuts import redirect
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
    fields: List[Tuple[str, str]] = [
        ("leaver_name", "Leaver's name"),
        ("security_clearance", "Security Clearance level"),
        ("work_email", "Email"),
        ("leaving_date", "Leaving date"),
        ("last_working_day", "Last working day"),
        ("days_until_last_working_day", "Days left"),
        ("reported_on", "Reported on"),
        ("complete", "Status"),
    ]

    def __init__(
        self,
        show_complete: bool = False,
        show_incomplete: bool = False,
    ) -> None:
        super().__init__()
        self.show_complete = show_complete
        self.show_incomplete = show_incomplete

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        initial["query"] = self.query
        return initial

    def get_leaving_requests(
        self,
        order_by: Optional[str] = None,
        order_direction: Literal["asc", "desc"] = "asc",
    ) -> QuerySet[LeavingRequest]:
        leaving_requests: QuerySet[LeavingRequest] = LeavingRequest.objects.all()
        complete_field = self.get_complete_field()
        if complete_field:
            if not self.show_complete:
                leaving_requests = leaving_requests.exclude(
                    **{complete_field + "__isnull": False}
                )
            if not self.show_incomplete:
                leaving_requests = leaving_requests.exclude(
                    **{complete_field + "__isnull": True}
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

        # Add annotations to make ordering easier
        leaving_requests = leaving_requests.annotate(
            # Concatonate first and last name. /PS-IGNORE
            leaver_name=Concat(
                "leaver_activitystream_user__first_name",
                Value(" "),
                "leaver_activitystream_user__last_name",
            ),
        )

        if order_by:
            if order_direction == "asc":
                leaving_requests = leaving_requests.order_by(order_by)
            else:
                leaving_requests = leaving_requests.order_by(f"-{order_by}")

        # Return filtered and searched leaving requests
        return leaving_requests

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        self.query = request.GET.get("query", "")
        self.table_header = self.get_table_header()
        self.order_by, self.order_direction = self.get_ordering(request)
        self.leaving_requests = self.get_leaving_requests(
            order_by=self.order_by,
            order_direction=self.order_direction,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_leaving_request_data(self) -> List[Dict[str, str]]:
        fields_to_display = [field[0] for field in self.fields]
        lr_results_data: List[Dict[str, str]] = []
        for lr in self.leaving_requests:
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
                "last_working_day": "Not yet known",
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

            fields_to_display_and_link = fields_to_display + ["link"]

            # Strip out any content we don't want to show.
            lr_result_data = {
                key: value
                for key, value in lr_result_data.items()
                if key in fields_to_display_and_link
            }
            # Sort the dict by the order of the fields.
            lr_result_data = OrderedDict(
                sorted(
                    lr_result_data.items(),
                    key=lambda x: fields_to_display_and_link.index(x[0]),
                )
            )
            lr_results_data.append(lr_result_data)
        return lr_results_data

    def get_table_header(self) -> List[Tuple[str, str, Dict[str, Optional[str]]]]:
        table_header = []
        field_order_by_mapping: Dict[str, str] = {
            "leaver_name": "leaver_name",
            "leaving_date": "leaving_date",
            "last_working_day": "last_day",
        }
        field_order_direction_mapping: Dict[str, str] = {
            "last_working_dat": "asc",
        }

        for field in self.fields:
            table_header.append(
                (
                    field[0],
                    field[1],
                    {
                        "order_by_field_name": field_order_by_mapping.get(
                            field[0],
                            None,
                        ),
                        "order_by_direction": field_order_direction_mapping.get(
                            field[0],
                            None,
                        ),
                    },
                )
            )

        return table_header

    def get_ordering(
        self, request: HttpRequest
    ) -> Tuple[Optional[str], Literal["asc", "desc"]]:
        assert self.table_header

        order_by = request.GET.get("order_by", "last_working_day")
        object_ordering_field_name = None
        object_ordering_direction = request.GET.get("order_direction", "asc")

        for header_item in self.table_header:
            if header_item[0] == order_by:
                object_ordering_field_name = header_item[2].get("order_by_field_name")
                object_ordering_direction = (
                    header_item[2]["order_by_direction"] or object_ordering_direction
                )
                break

        if object_ordering_direction not in ["asc", "desc"]:
            object_ordering_direction = "asc"

        object_ordering_direction = cast(
            Literal["asc", "desc"],
            object_ordering_direction,
        )
        return object_ordering_field_name, object_ordering_direction

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            request=self.request,
            show_complete=self.show_complete,
            show_incomplete=self.show_incomplete,
            table_header=self.get_table_header(),
            order_by=self.order_by,
            order_direction=self.order_direction,
        )

        # Set object type name
        object_type_name = self.get_object_type_name()
        context.update(
            object_type_name=object_type_name,
            page_title=self.get_page_title(object_type_name),
        )

        lr_results_data = self.get_leaving_request_data()

        # Paginate the results
        paginator = Paginator(lr_results_data, 20)
        page_number: int = int(self.request.GET.get("page", 1))
        page = paginator.page(page_number)

        pagination_pages: Set[int] = set([1])

        if page_number != 1:
            pagination_pages.add(page_number - 1)
        pagination_pages.add(page_number)
        if page_number != paginator.num_pages:
            pagination_pages.add(page_number + 1)
            pagination_pages.add(paginator.num_pages)

        # Cleanup the pagination pages set
        pagination_pages.discard(0)
        # Sort the set
        pagination_pages = set(sorted(pagination_pages))

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

    def get_summary_view(self) -> str:
        return self.summary_view

    def get_confirmation_view(self) -> str:
        return self.confirmation_view

    def get_complete_field(self) -> str:
        return self.complete_field

    def form_valid(self, form: Any) -> HttpResponse:
        self.query = form.cleaned_data["query"]
        return redirect(
            f"{self.request.path}"
            f"?query={self.query}"
            f"&show_complete={self.show_complete}"
            f"&show_incomplete={self.show_incomplete}"
        )
