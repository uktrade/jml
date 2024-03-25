from typing import Dict, List, Optional

from rest_framework import serializers

from leavers.models import LeavingRequest
from leavers.serializers import LeavingRequestSerializer


class BEISLeavingRequestSerializer(LeavingRequestSerializer):
    service_now_leaver_email = serializers.SerializerMethodField()
    service_now_leaver_user_sys_id = serializers.SerializerMethodField()
    service_now_line_manager_email = serializers.SerializerMethodField()
    service_now_line_manager_user_sys_id = serializers.SerializerMethodField()
    service_now_users_assets = serializers.SerializerMethodField()
    service_now_location = serializers.SerializerMethodField()
    service_now_collection_details = serializers.SerializerMethodField()

    class Meta:
        model = LeavingRequestSerializer.Meta.model
        fields = [
            "uuid",
            "leaving_date",
            "reason_for_leaving",
            "security_clearance",
            "service_now_leaver_email",
            "service_now_leaver_user_sys_id",
            "service_now_line_manager_email",
            "service_now_line_manager_user_sys_id",
            "service_now_users_assets",
            "service_now_location",
            "service_now_collection_details",
        ]

    def get_service_now_leaver_email(
        self,
        obj: LeavingRequest,
    ) -> Optional[str]:
        return "not.a.real@servicenow.email"  # /PS-IGNORE

    def get_service_now_leaver_user_sys_id(
        self,
        obj: LeavingRequest,
    ) -> Optional[str]:
        return "1234567890"

    def get_service_now_line_manager_email(
        self,
        obj: LeavingRequest,
    ) -> Optional[str]:
        return "not.a.real@servicenow.email"  # /PS-IGNORE

    def get_service_now_line_manager_user_sys_id(
        self,
        obj: LeavingRequest,
    ) -> Optional[str]:
        return "1234567890"

    def get_service_now_users_assets(
        self,
        obj: LeavingRequest,
    ) -> Optional[List[Dict[str, str]]]:
        return [
            {
                "asset_tag": "THIS IS NOT THE FINAL STRUCTURE!",
                "asset_name": "THIS IS NOT THE FINAL STRUCTURE!",
            }
            for _ in range(3)
        ]

    def get_service_now_collection_details(
        self,
        obj: LeavingRequest,
    ) -> Optional[Dict[str, str]]:
        return {
            "contact_telephone_for_collection": "01234567890",
            "contact_email_for_delivery_collection": "not.a.real@example.email",  # /PS-IGNORE
            "collection_address_for_remote_leaver": "EXAMPLE ADDRESS, EXAMPLE TOWN",
            "collection_postcode_for_remote_leaver": "PO57 C0D3",
        }

    def get_service_now_location(
        self,
        obj: LeavingRequest,
    ) -> Optional[str]:
        return "EXAMPLE LOCATION"
