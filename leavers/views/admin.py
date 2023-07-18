import json
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple, Union, cast
from uuid import UUID

from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import JSONField, Q
from django.db.models.fields import Field
from django.db.models.fields.related import (
    ForeignKey,
    ManyToManyField,
    ManyToOneRel,
    OneToOneField,
)
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import FormView
from django_workflow_engine.models import Flow

from core.people_data import get_people_data_interface
from core.utils.staff_index import get_csd_for_activitystream_user
from core.views import BaseTemplateView
from leavers.forms.admin import ManuallyOffboardedFromUKSBSForm
from leavers.models import LeavingRequest, TaskLog
from leavers.types import LeavingReason, LeavingRequestLineReport
from leavers.views import base

LEAVING_REQUEST_QUERIES = {
    "leaver_not_submitted": Q(leaver_complete__isnull=True),
    "leaver_submitted": Q(leaver_complete__isnull=False),
    "line_manager_not_submitted": Q(
        leaver_complete__isnull=False,
        line_manager_complete__isnull=True,
    ),
    "submitted_retirement": Q(
        leaver_complete__isnull=False,
        line_manager_complete__isnull=False,
        reason_for_leaving=LeavingReason.RETIREMENT.value,
    ),
    "submitted_ill_heallth_retirement": Q(
        leaver_complete__isnull=False,
        line_manager_complete__isnull=False,
        reason_for_leaving=LeavingReason.ILL_HEALTH_RETIREMENT.value,
    ),
}


class LeaversAdminView(BaseTemplateView):
    template_name = "leavers/admin/index.html"

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        people_data_interface = get_people_data_interface()
        context = super().get_context_data(**kwargs)
        admin_lr_view = reverse("admin-leaving-request-listing")
        context.update(
            page_title="Leavers admin",
            leaving_requests_all_url=admin_lr_view,
            leaver_not_submitted=LeavingRequest.objects.filter(
                LEAVING_REQUEST_QUERIES["leaver_not_submitted"],
            ),
            leaver_not_submitted_url=admin_lr_view
            + "?custom_filter=leaver_not_submitted",
            leaver_submitted=LeavingRequest.objects.filter(
                LEAVING_REQUEST_QUERIES["leaver_submitted"],
            ),
            leaver_submitted_url=admin_lr_view + "?custom_filter=leaver_submitted",
            line_manager_not_submitted=LeavingRequest.objects.filter(
                LEAVING_REQUEST_QUERIES["line_manager_not_submitted"],
            ),
            line_manager_not_submitted_url=admin_lr_view
            + "?custom_filter=line_manager_not_submitted",
            submitted_retirement=LeavingRequest.objects.filter(
                LEAVING_REQUEST_QUERIES["submitted_retirement"],
            ),
            submitted_retirement_url=admin_lr_view
            + "?custom_filter=submitted_retirement",
            submitted_ill_heallth_retirement=LeavingRequest.objects.filter(
                LEAVING_REQUEST_QUERIES["submitted_ill_heallth_retirement"],
            ),
            submitted_ill_heallth_retirement_url=admin_lr_view
            + "?custom_filter=submitted_ill_heallth_retirement",
            emails_with_person_ids=people_data_interface.get_emails_with_multiple_person_ids(),
            oddly_finished_workflows=Flow.objects.filter(
                finished__isnull=False, tasks__done=False
            ),
        )
        return context


class LeavingRequestListingView(UserPassesTestMixin, base.LeavingRequestListing):
    template_name = "leavers/admin/leaving_request/listing.html"

    confirmation_view = "admin-leaving-request-detail"
    summary_view = "admin-leaving-request-detail"
    page_title = ""
    fields: List[Tuple[str, str]] = [
        ("leaver_name", "Leaver's name"),
        ("work_email", "Email"),
        ("leaving_date", "Leaving date"),
        ("last_working_day", "Last working day"),
        ("days_until_last_working_day", "Days left"),
        ("reported_on", "Reported on"),
        ("complete", "Status"),
    ]

    def test_func(self):
        return self.request.user.is_staff

    def get_page_title(self, object_type_name: str) -> str:
        page_title = super().get_page_title(object_type_name)

        if self.request.GET.get("custom_filter"):
            return f"{page_title} - FILTERED"
        return page_title

    def get_leaving_requests(
        self,
        order_by: Optional[str] = None,
        order_direction: Literal["asc", "desc"] = "asc",
    ):
        leaving_requests = super().get_leaving_requests()

        custom_filter: Optional[str] = self.request.GET.get("custom_filter")
        if custom_filter in LEAVING_REQUEST_QUERIES:
            leaving_requests = leaving_requests.filter(
                LEAVING_REQUEST_QUERIES[custom_filter]
            )
        return leaving_requests


class LeavingRequestDetailView(UserPassesTestMixin, BaseTemplateView):
    template_name = "leavers/admin/leaving_request/detail.html"

    def test_func(self):
        return self.request.user.is_staff

    def dispatch(self, request, *args, **kwargs):
        self.leaving_request = get_object_or_404(
            LeavingRequest, uuid=kwargs["leaving_request_uuid"]
        )
        return super().dispatch(request, *args, **kwargs)

    def format_list(self, value: List) -> str:
        formatted_value = "<ul class='govuk-list govuk-list--bullet'>"
        for item in value:
            if type(item) != str:
                item = self.format_value(field=None, value=item)
            formatted_value += f"<li>{item}</li>"
        formatted_value += "</ul>"
        return mark_safe(formatted_value)

    def format_models(
        self, field: Optional[Union[Field, ForeignObjectRel]], value: Any
    ) -> Optional[str]:
        value_type = type(value)

        if value_type == Flow:
            value_obj = cast(Flow, value)
            flow_url = reverse("flow", kwargs={"pk": value_obj.pk})
            return mark_safe(f"<a class='govuk-link' href='{flow_url}'>Workflow</a>")

        if value_type == TaskLog:
            value_obj = cast(TaskLog, value)
            return f"TaskLog: '{value_obj.task_name}'"

        return None

    def format_json_field(
        self, field: Optional[Union[Field, ForeignObjectRel]], value: Any
    ) -> str:
        if field and field.name == "line_reports":
            formatted_value = ""
            for index, line_report in enumerate(value):
                line_report_obj = cast(LeavingRequestLineReport, line_report)
                formatted_value += (
                    f"Line Report Name: {line_report_obj['name']}<br>"
                    f"Line Report Email: {line_report_obj['email']}<br>"
                )
                line_manager = line_report_obj.get("line_manager")
                if line_manager:
                    formatted_value += (
                        f"Line Manager Name: {line_manager['name']}<br>"
                        f"Line Manager Email: {line_manager['email']}<br>"
                    )

                if index + 1 != len(value):
                    formatted_value += "<hr>"

            return mark_safe(formatted_value)
        return json.dumps(value)

    def format_value(
        self, field: Optional[Union[Field, ForeignObjectRel]], value: Any
    ) -> str:
        if value is None:
            return "-"

        value_type = type(value)
        if value_type in [str, int, bool, UUID]:
            return str(value)

        if value_type == datetime:
            return value

        field_type: Any = ""
        if field:
            field_type = type(field)

        if field_type == JSONField:
            return self.format_json_field(field=field, value=value)

        if value_type == list:
            return self.format_list(value=value)

        model_value = self.format_models(field=field, value=value)
        if model_value:
            return model_value

        if field_type in [ForeignKey, OneToOneField, ManyToOneRel]:
            return value

        if field_type == ManyToManyField:
            value_list: List[str] = [obj for obj in value.all()]
            return self.format_value(field=field, value=value_list)

        return f"{value_type}/{field_type} needs formatting"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        leaving_request_field_values: List[Tuple[str, str]] = []
        for field in self.leaving_request._meta.get_fields():
            value = getattr(self.leaving_request, field.name)
            formatted_value = self.format_value(field=field, value=value)

            leaving_request_field_values.append(
                (
                    field.name,
                    formatted_value,
                )
            )

        context.update(
            leaving_request=self.leaving_request,
            leaving_request_field_values=leaving_request_field_values,
            leaver=get_csd_for_activitystream_user(
                activitystream_user=self.leaving_request.leaver_activitystream_user
            ),
            manager=get_csd_for_activitystream_user(
                activitystream_user=self.leaving_request.manager_activitystream_user
            ),
            processing_manager=get_csd_for_activitystream_user(
                activitystream_user=self.leaving_request.processing_manager_activitystream_user
            ),
            data_recipient=get_csd_for_activitystream_user(
                activitystream_user=self.leaving_request.data_recipient_activitystream_user
            ),
        )
        return context


class LeavingRequestManuallyOffboarded(UserPassesTestMixin, FormView, BaseTemplateView):
    template_name = "leavers/admin/leaving_request/manual_offboard_from_uksbs.html"
    form_class = ManuallyOffboardedFromUKSBSForm

    def test_func(self):
        return self.request.user.is_staff

    def get_success_url(self) -> str:
        return reverse(
            "admin-leaving-request-detail",
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["leaving_request_uuid"] = self.leaving_request.uuid
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.leaving_request = get_object_or_404(
            LeavingRequest, uuid=kwargs["leaving_request_uuid"]
        )
        if self.leaving_request.manually_offboarded_from_uksbs:
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leaver_name = self.leaving_request.get_leaver_name()
        context.update(
            page_title=f"Mark '{leaver_name}' as offboarded from UK SBS ",
            leaver_name=leaver_name,
            leaving_request_uuid=self.leaving_request.uuid,
        )
        return context

    def form_valid(self, form) -> HttpResponse:
        self.leaving_request.manually_offboarded_from_uksbs = (
            self.leaving_request.task_logs.create(
                user=self.request.user,
                task_name="Leaver has been manually offboarded from UK SBS",
                reference="LeavingRequest.manually_offboarded_from_uksbs",
            )
        )
        self.leaving_request.save()
        return super().form_valid(form)

    def get_back_link_url(self):
        return reverse(
            "admin-leaving-request-detail",
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )


class OfflineServiceNowAdmin(BaseTemplateView):
    template_name = "leavers/admin/servicenow_offline.html"

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        leaving_requests = LeavingRequest.objects.filter(
            line_manager_complete__isnull=False,
            service_now_offline=True,
            line_manager_service_now_complete__isnull=True,
        )
        data = []
        for lr in leaving_requests:
            leaver_name = lr.get_leaver_name()
            leaver_email = lr.get_leaver_email()
            manager_name = lr.get_line_manager().name
            manager_emails = lr.get_line_manager().get_email_addresses_for_contact()
            data.append(
                {
                    "leaver_name": leaver_name,
                    "leaver_email": leaver_email,
                    "manager_name": manager_name,
                    "manager_emails": ",".join(manager_emails),
                    "service_now_offline_link": reverse(
                        "line-manager-offline-service-now-details",
                        kwargs={"leaving_request_uuid": lr.uuid},
                    ),
                }
            )
        context.update(
            page_title="ServiceNow Offline not complete",
            data=data,
        )
        return context
