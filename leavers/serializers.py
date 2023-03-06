from typing import cast

from django_workflow_engine.models import Flow
from rest_framework import serializers

from leavers.models import LeavingRequest


class LeavingRequestSerializer(serializers.ModelSerializer):
    last_working_day = serializers.SerializerMethodField()
    leaving_date = serializers.SerializerMethodField()
    leaving_reason = serializers.CharField(source="reason_for_leaving")
    sre_tasks_complete = serializers.BooleanField(source="sre_complete")
    security_building_pass_tasks_complete = serializers.BooleanField(
        source="security_team_building_pass_complete",
    )
    security_rosa_kit_tasks_complete = serializers.BooleanField(
        source="security_team_rosa_kit_complete",
    )
    payroll_request_sent = serializers.SerializerMethodField()

    class Meta:
        model = LeavingRequest
        fields = [
            "uuid",
            "staff_type",
            "is_rosa_user",
            "holds_government_procurement_card",
        ]

    def get_last_working_day(self, obj: LeavingRequest) -> str:
        last_working_day = obj.get_last_day()
        assert last_working_day
        return str(last_working_day.date())

    def get_leaving_date(self, obj: LeavingRequest) -> str:
        leaving_date = obj.get_leaving_date()
        assert leaving_date
        return str(leaving_date.date())

    def get_payroll_request_sent(self, obj: LeavingRequest) -> bool:
        payroll_request_sent: bool = False
        flow = cast(Flow, obj.flow)
        if (
            flow
            and flow.tasks.filter(
                step_id="send_uksbs_leaver_details", done=True
            ).exists()
        ):
            payroll_request_sent = True
        return payroll_request_sent
