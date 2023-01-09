from typing import Any, Dict, cast

from dit_activity_stream.client import ActivityStreamClient
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.http import HttpRequest
from django_workflow_engine.models import Flow

from leavers.models import LeavingRequest

User = get_user_model()


class ActivityStreamLeavingRequestClient(ActivityStreamClient):
    object_uuid_field: str = "uuid"
    object_last_modified_field: str = "last_modified"

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return LeavingRequest.objects.filter(line_manager_complete__isnull=False)

    def render_object(self, object: LeavingRequest) -> Dict[str, Any]:
        last_working_day = object.get_last_day()
        leaving_date = object.get_leaving_date()

        assert last_working_day
        assert leaving_date

        payroll_request_sent: bool = False
        flow = cast(Flow, object.flow)
        if (
            flow
            and flow.tasks.filter(
                step_id="send_uksbs_leaver_details", done=True
            ).exists()
        ):
            payroll_request_sent = True

        return {
            "uuid": str(object.uuid),
            "last_working_day": str(last_working_day.date()),
            "leaving_date": str(leaving_date.date()),
            "staff_type": object.staff_type,
            "leaving_reason": object.reason_for_leaving,
            "is_rosa_user": object.is_rosa_user,
            "holds_government_procurement_card": object.holds_government_procurement_card,
            "sre_tasks_complete": bool(object.sre_complete),
            "security_building_pass_tasks_complete": bool(
                object.security_team_building_pass_complete
            ),
            "security_rosa_kit_tasks_complete": bool(
                object.security_team_rosa_kit_complete
            ),
            "payroll_request_sent": payroll_request_sent,
        }
