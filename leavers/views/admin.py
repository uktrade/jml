import json
from datetime import datetime
from typing import Any, List, Optional, Tuple, Union, cast
from uuid import UUID

from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import JSONField
from django.db.models.fields import Field
from django.db.models.fields.related import (
    ForeignKey,
    ManyToManyField,
    ManyToOneRel,
    OneToOneField,
)
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from django_workflow_engine.models import Flow

from activity_stream.models import ActivityStreamStaffSSOUser
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    consolidate_staff_documents,
    get_staff_document_from_staff_index,
)
from leavers.models import LeavingRequest, TaskLog
from leavers.types import LeavingRequestLineReport
from leavers.views import base


class LeavingRequestListingView(base.LeavingRequestListing):
    template_name = "leavers/admin/leaving_request/listing.html"

    confirmation_view = "admin-leaving-request-detail"
    summary_view = "admin-leaving-request-detail"
    page_title = ""
    service_name = "Leaving DIT: Leaving Request Admin"
    fields = [
        "leaver_name",
        "work_email",
        "leaving_date",
        "last_working_day",
        "days_until_last_working_day",
        "reported_on",
    ]

    def test_func(self):
        return self.request.user.is_staff


class LeavingRequestDetailView(UserPassesTestMixin, TemplateView):
    template_name = "leavers/admin/leaving_request/detail.html"

    def test_func(self):
        return self.request.user.is_staff

    def dispatch(self, request, *args, **kwargs):
        self.leaving_request = get_object_or_404(
            LeavingRequest, uuid=kwargs["leaving_request_id"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_csd_for_activitystream_user(
        self, activitystream_user: Optional[ActivityStreamStaffSSOUser]
    ) -> Optional[ConsolidatedStaffDocument]:
        if not activitystream_user:
            return None

        sso_email_user_id = activitystream_user.email_user_id
        staff_document = get_staff_document_from_staff_index(
            sso_email_user_id=sso_email_user_id,
        )
        if not staff_document:
            return None

        consolidated_staff_documents = consolidate_staff_documents(
            staff_documents=[staff_document],
        )
        return consolidated_staff_documents[0]

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
                    f"New line report? {line_report_obj['new_line_report']}<br>"
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
            leaver=self.get_csd_for_activitystream_user(
                activitystream_user=self.leaving_request.leaver_activitystream_user
            ),
            manager=self.get_csd_for_activitystream_user(
                activitystream_user=self.leaving_request.manager_activitystream_user
            ),
            processing_manager=self.get_csd_for_activitystream_user(
                activitystream_user=self.leaving_request.processing_manager_activitystream_user
            ),
            data_recipient=self.get_csd_for_activitystream_user(
                activitystream_user=self.leaving_request.data_recipient_activitystream_user
            ),
        )
        return context
