from typing import Any, Dict, Literal, Optional, Tuple

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic.edit import FormView

from leavers.models import LeavingRequest, TaskLog


class TaskConfirmationView(
    UserPassesTestMixin,
    FormView,
):
    leaving_request = None
    complete_field: str = ""

    # Field mapping from the Form field name to the LeavingRequest field name (with task messages)
    field_mapping: Dict[str, Tuple[str, str, str]] = {}

    def test_func(self):
        raise NotImplementedError()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.leaving_request = get_object_or_404(
            LeavingRequest,
            uuid=self.kwargs.get("leaving_request_id", None),
        )
        complete: bool = getattr(self.leaving_request, self.complete_field)
        if complete:
            # TODO: Update with link to the summary page
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            leaver_name=self.leaving_request.get_leaver_name(),
            leaving_date=self.leaving_request.last_day,
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
        new_task_log = self.leaving_request.task_logs.create(
            user=self.request.user,
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
