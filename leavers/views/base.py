from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional, Tuple, cast

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.postgres.search import SearchVector
from django.core.paginator import Paginator
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic.edit import FormView

from leavers.forms import data_processor as data_processor_forms
from leavers.forms.leaver import SecurityClearance
from leavers.models import LeavingRequest, TaskLog
from user.models import User


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
        # Filter out any that haven't been completed by the Line Manager.
        leaving_requests: QuerySet[
            LeavingRequest
        ] = LeavingRequest.objects.all().exclude(line_manager_complete__isnull=True)
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
            leaving_date = lr.get_leaving_date()
            last_day = lr.get_last_day()

            assert leaving_date
            assert last_day
            assert lr.line_manager_complete

            is_complete = getattr(lr, self.get_complete_field())
            link = reverse_lazy(
                self.get_confirmation_view(), kwargs={"leaving_request_id": lr.uuid}
            )
            if is_complete:
                link = reverse_lazy(
                    self.get_summary_view(), kwargs={"leaving_request_id": lr.uuid}
                )

            days_until_last_working_day: timedelta = (
                last_day.date() - timezone.now().date()
            )

            lr_results_data.append(
                {
                    "link": link,
                    "leaver_name": lr.get_leaver_name(),
                    "security_clearance": SecurityClearance(
                        lr.security_clearance
                    ).label,
                    "work_email": lr.get_leaver_email(),
                    "leaving_date": leaving_date.date(),
                    "last_working_day": last_day.date(),
                    "days_until_last_working_day": days_until_last_working_day.days,
                    "reported_on": lr.line_manager_complete.date(),
                    "complete": bool(getattr(lr, self.get_complete_field())),
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


class TaskConfirmationView(
    UserPassesTestMixin,
    FormView,
):
    leaving_request = None
    complete_field: str = ""
    page_title: str = ""

    # Field mapping from the Form field name to the LeavingRequest field name (with task messages)
    field_mapping: Dict[str, Tuple[str, str, str]] = {}

    def test_func(self):
        raise NotImplementedError()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        leaving_datetime = self.leaving_request.get_leaving_date()
        leaving_date: Optional[datetime] = None
        if leaving_datetime:
            leaving_date = leaving_datetime.date()

        last_day_datetime = self.leaving_request.get_last_day()
        last_day: Optional[datetime] = None
        if last_day_datetime:
            last_day = last_day_datetime.date()

        context.update(
            page_title=self.page_title,
            leaver_name=self.leaving_request.get_leaver_name(),
            leaver_email=self.leaving_request.get_leaver_email(),
            leaving_date=leaving_date,
            last_day=last_day,
            complete=bool(getattr(self.leaving_request, self.complete_field)),
        )

        return context

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()

        for key, value in self.field_mapping.items():
            leaving_request_value: TaskLog = getattr(self.leaving_request, value[0])
            initial[key] = bool(leaving_request_value)

        return initial

    def format_task_name(self, field_key: str, task_name: str, field_value: Any) -> str:
        return task_name

    def create_task(
        self,
        leaving_request_field_name: str,
        task_name: str,
        add_to_leaving_request: bool,
    ) -> None:
        assert self.leaving_request
        user = cast(User, self.request.user)

        new_task_log = self.leaving_request.task_logs.create(
            user=user,
            task_name=task_name,
        )
        if add_to_leaving_request:
            setattr(
                self.leaving_request,
                leaving_request_field_name,
                new_task_log,
            )

    def form_valid_checkbox(
        self,
        existing_task_log: Optional[TaskLog],
        leaving_request_field_name: str,
        new_value: bool,
        task_name_confirmed: str,
        task_name_unconfirmed: str,
    ) -> None:
        if new_value and not existing_task_log:
            self.create_task(
                leaving_request_field_name=leaving_request_field_name,
                task_name=task_name_confirmed,
                add_to_leaving_request=True,
            )
        elif not new_value:
            self.create_task(
                leaving_request_field_name=leaving_request_field_name,
                task_name=task_name_unconfirmed,
                add_to_leaving_request=False,
            )
            # Remove the value from the LeavingRequest so we know this checkbox
            # is unchecked.
            setattr(
                self.leaving_request,
                leaving_request_field_name,
                None,
            )

    def form_valid_choices(
        self,
        existing_task_log: Optional[TaskLog],
        form_field_name: str,
        leaving_request_field_name: str,
        old_value: Optional[str],
        new_value: str,
        task_name_confirmed: str,
        task_name_unconfirmed: str,
    ) -> None:
        if existing_task_log and new_value != old_value:
            # There was an existing task log, and the value has changed.

            # Create a new task log to unconfirm the old action
            old_task_name_unconfirmed = self.format_task_name(
                field_key=form_field_name,
                task_name=task_name_unconfirmed,
                field_value=old_value,
            )
            self.create_task(
                leaving_request_field_name=leaving_request_field_name,
                task_name=old_task_name_unconfirmed,
                add_to_leaving_request=False,
            )

            # Only create a news task log if the new value is set (not an empty string)
            if new_value:
                # Create a new task log to confirm the new action
                self.create_task(
                    leaving_request_field_name=leaving_request_field_name,
                    task_name=task_name_confirmed,
                    add_to_leaving_request=True,
                )
            else:
                # The new value is empty, so remove the value from the LeavingRequest
                setattr(
                    self.leaving_request,
                    leaving_request_field_name,
                    None,
                )
        elif not existing_task_log and new_value:
            # There was no existing task log, there is a value set.

            # Create a new task log to confirm the new action
            self.create_task(
                leaving_request_field_name=leaving_request_field_name,
                task_name=task_name_confirmed,
                add_to_leaving_request=True,
            )

    def form_valid(self, form):
        submission_type: Literal["save", "submit"] = "save"
        if "submit" in form.data:
            submission_type = "submit"

        for key, value in self.field_mapping.items():
            if key not in form.changed_data:
                continue

            existing_task_log: Optional[TaskLog] = getattr(
                self.leaving_request, value[0]
            )

            task_name_confirmed = self.format_task_name(
                field_key=key,
                task_name=value[1],
                field_value=form.cleaned_data[key],
            )
            task_name_unconfirmed = self.format_task_name(
                field_key=key,
                task_name=value[2],
                field_value=form.cleaned_data[key],
            )

            # Checkbox field
            if isinstance(form.cleaned_data[key], bool):
                self.form_valid_checkbox(
                    existing_task_log=existing_task_log,
                    leaving_request_field_name=value[0],
                    new_value=form.cleaned_data[key],
                    task_name_confirmed=task_name_confirmed,
                    task_name_unconfirmed=task_name_unconfirmed,
                )

            # Choice field
            if isinstance(form.cleaned_data[key], str):
                old_value: Optional[str] = form.initial.get(key, None)
                new_value: str = form.cleaned_data[key]

                self.form_valid_choices(
                    existing_task_log=existing_task_log,
                    form_field_name=key,
                    leaving_request_field_name=value[0],
                    old_value=old_value,
                    new_value=new_value,
                    task_name_confirmed=task_name_confirmed,
                    task_name_unconfirmed=task_name_unconfirmed,
                )

            # Save the changes
            self.leaving_request.save()

        if submission_type == "submit":
            setattr(
                self.leaving_request,
                self.complete_field,
                timezone.now(),
            )
            self.leaving_request.save()

        return super().form_valid(form)
