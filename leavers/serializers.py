from datetime import datetime
from typing import Optional, cast

from django_workflow_engine.models import Flow, TaskStatus
from rest_framework import serializers

from leavers.models import LeavingRequest


class LeavingRequestSerializer(serializers.ModelSerializer):
    last_working_day = serializers.DateTimeField(source="get_last_day")
    leaving_date = serializers.DateTimeField(source="get_leaving_date")
    security_clearance = serializers.SerializerMethodField()
    security_team_building_pass_destroyed = serializers.BooleanField(
        source="security_pass_destroyed"
    )
    security_team_building_pass_disabled = serializers.BooleanField(
        source="security_pass_disabled"
    )
    security_team_building_pass_returned = serializers.BooleanField(
        source="security_pass_returned"
    )
    security_team_security_clearance_status = serializers.SerializerMethodField()
    security_team_rosa_mobile_status = serializers.SerializerMethodField()
    security_team_rosa_laptop_status = serializers.SerializerMethodField()
    security_team_rosa_key_status = serializers.SerializerMethodField()
    payroll_request_sent = serializers.SerializerMethodField()

    class Meta:
        model = LeavingRequest
        fields = [
            "uuid",
            "staff_type",
            "last_working_day",
            "leaving_date",
            "reason_for_leaving",
            "is_rosa_user",
            "holds_government_procurement_card",
            "security_clearance",
            "completed_by_leaver",
            "leaver_complete",
            "line_manager_complete",
            "line_manager_service_now_complete",
            "sre_complete",
            "security_team_building_pass_destroyed",
            "security_team_building_pass_disabled",
            "security_team_building_pass_returned",
            "security_team_security_clearance_status",
            "security_team_building_pass_complete",
            "security_team_rosa_mobile_status",
            "security_team_rosa_laptop_status",
            "security_team_rosa_key_status",
            "security_team_rosa_kit_complete",
            "security_team_complete",
            "payroll_request_sent",
        ]

    def get_security_clearance(self, obj: LeavingRequest) -> Optional[str]:
        security_clearance = obj.get_security_clearance()
        if not security_clearance:
            return None
        return security_clearance.value

    def get_security_team_security_clearance_status(
        self, obj: LeavingRequest
    ) -> Optional[str]:
        task_log = obj.security_clearance_status
        if not task_log:
            return None
        return task_log.value

    def get_security_team_rosa_mobile_status(
        self, obj: LeavingRequest
    ) -> Optional[str]:
        task_log = obj.rosa_mobile_returned
        if not task_log:
            return None
        return task_log.value

    def get_security_team_rosa_laptop_status(
        self, obj: LeavingRequest
    ) -> Optional[str]:
        task_log = obj.rosa_laptop_returned
        if not task_log:
            return None
        return task_log.value

    def get_security_team_rosa_key_status(self, obj: LeavingRequest) -> Optional[str]:
        task_log = obj.rosa_key_returned
        if not task_log:
            return None
        return task_log.value

    def get_payroll_request_sent(self, obj: LeavingRequest) -> Optional[datetime]:
        # TODO: Fix this once Django Workflow Engine has had Task Records fixed.
        return None
        flow = cast(Flow, obj.flow)
        if not flow:
            return None
        send_uksbs_task: Optional[TaskStatus] = flow.tasks.filter(
            step_id="send_uksbs_leaver_details", done=True
        ).first()
        if not send_uksbs_task:
            return None
        return send_uksbs_task.executed_at
