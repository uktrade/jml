from collections import OrderedDict
from datetime import timedelta
from typing import Any, Dict, List, Literal, Optional, Tuple, cast

from django.contrib.postgres.search import SearchVector
from django.core.paginator import Paginator
from django.db.models import Case, Value, When
from django.db.models.functions import Concat
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import View
from django.views.generic.edit import FormView

from activity_stream.models import ActivityStreamStaffSSOUser
from core.people_finder import get_people_finder_interface
from core.views import BaseTemplateView
from leavers.forms import data_processor as data_processor_forms
from leavers.models import LeaverInformation, LeavingRequest
from user.models import User


class SaveAndCloseViewMixin:
    save_and_close: bool = False

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        if "save_and_close" in self.request.POST:
            self.save_and_close = True
            cleaned_post = self.request.POST.copy()
            cleaned_post.update(submit=cleaned_post["save_and_close"])  # type: ignore
            del cleaned_post["save_and_close"]
            self.request.POST = cleaned_post  # type: ignore
        return super().post(request, *args, **kwargs)


class LeavingRequestListing(
    BaseTemplateView,
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
            leaver_info_name=Concat(
                "leaver_information__leaver_first_name",
                Value(" "),
                "leaver_information__leaver_last_name",
            ),
            leaver_as_name=Concat(
                "leaver_activitystream_user__first_name",
                Value(" "),
                "leaver_activitystream_user__last_name",
            ),
            leaver_name=Case(
                When(
                    leaver_information__leaver_first_name__isnull=False,
                    leaver_information__leaver_last_name__isnull=False,
                    then="leaver_info_name",
                ),
                default="leaver_as_name",
            ),
            leaving_date_agg=Case(
                When(
                    leaving_date__isnull=False,
                    then="leaving_date",
                ),
                default="leaver_information__leaving_date",
            ),
            last_day_agg=Case(
                When(
                    last_day__isnull=False,
                    then="last_day",
                ),
                default="leaver_information__last_day",
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
                self.get_confirmation_view(), kwargs={"leaving_request_uuid": lr.uuid}
            )
            if is_complete:
                link = reverse_lazy(
                    self.get_summary_view(), kwargs={"leaving_request_uuid": lr.uuid}
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
                security_clearance = lr.get_security_clearance()
                if security_clearance:
                    lr_result_data.update(security_clearance=security_clearance.label)

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
            "leaving_date": "leaving_date_agg",
            "last_working_day": "last_day_agg",
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
            has_query=bool(self.query),
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
        paginator = Paginator(lr_results_data, 30)
        page_number: int = int(self.request.GET.get("page", 1))
        page = paginator.page(page_number)
        context.update(page=page, paginator=paginator)

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


class LeavingRequestViewMixin(View):
    people_finder_search = get_people_finder_interface()

    leaver_activitystream_user: ActivityStreamStaffSSOUser
    leaving_request: LeavingRequest
    leaver_info: LeaverInformation
    user_is_leaver: bool

    success_viewname: Optional[str] = None
    back_link_viewname: Optional[str] = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        user = cast(User, request.user)

        # 1 + len(prefetch_related) database queries
        self.leaving_request = (
            LeavingRequest.objects.select_related(
                "leaver_activitystream_user",
                "manager_activitystream_user",
            )
            .prefetch_related("leaver_information")
            .get(uuid=self.kwargs["leaving_request_uuid"])
        )
        self.leaver_activitystream_user = (
            self.leaving_request.leaver_activitystream_user
        )
        self.leaver_info = self.leaving_request.leaver_information.first()

        user_sso_user = user.get_sso_user()
        self.user_is_leaver = user_sso_user == self.leaver_activitystream_user

    def get_view_url(self, viewname, *args, **kwargs):
        kwargs.update(leaving_request_uuid=self.leaving_request.uuid)

        return reverse(viewname, args=args, kwargs=kwargs)

    def get_success_url(self):
        if not self.success_viewname:
            return super().get_success_url()

        return reverse(
            self.success_viewname,
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )

    def get_back_link_url(self):
        if not self.back_link_viewname:
            return super().get_back_link_url()

        return reverse(
            self.back_link_viewname,
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )

    def get_context_data(self, **kwargs):
        context = {
            "leaving_request": self.leaving_request,
            "user_is_leaver": self.user_is_leaver,
        }

        return super().get_context_data(**kwargs) | context

    def get_session(self):
        if "leaving_requests" not in self.request.session:
            self.request.session["leaving_requests"] = {}
        return self.request.session["leaving_requests"].get(
            self.leaving_request.pk,
            {},
        )

    def store_session(self, session):
        current_session = self.get_session()
        current_session.update(session)
        self.request.session["leaving_requests"][
            self.leaving_request.pk
        ] = current_session
        self.request.session.save()
