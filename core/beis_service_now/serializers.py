from typing import Dict, List, Optional

from rest_framework import serializers

from leavers.models import LeavingRequest
from leavers.serializers import LeavingRequestSerializer


class BEISLeavingRequestSerializer(LeavingRequestSerializer):
    service_now_leaver_emails = serializers.SerializerMethodField()
    service_now_leaver_user_sys_ids = serializers.SerializerMethodField()
    service_now_line_manager_emails = serializers.SerializerMethodField()
    service_now_line_manager_user_sys_ids = serializers.SerializerMethodField()
    service_now_users_assets = serializers.SerializerMethodField()
    service_now_additional_asset_information = serializers.SerializerMethodField()
    service_now_collection_details = serializers.SerializerMethodField()

    class Meta:
        model = LeavingRequestSerializer.Meta.model
        fields = [
            "uuid",
            "leaving_date",
            "reason_for_leaving",
            "security_clearance",
            "service_now_leaver_emails",
            "service_now_leaver_user_sys_ids",
            "service_now_line_manager_emails",
            "service_now_line_manager_user_sys_ids",
            "service_now_users_assets",
            "service_now_additional_asset_information",
            "service_now_collection_details",
        ]

    def get_service_now_leaver_emails(
        self,
        obj: LeavingRequest,
    ) -> Optional[str]:
        emails = obj.leaver_activitystream_user.service_now_users.all().values_list(
            "email", flat=True
        )
        if not emails:
            raise ValueError(
                f"Leaver {obj.leaver_activitystream_user} has no ServiceNow users"
            )
        return ",".join(emails)

    def get_service_now_leaver_user_sys_ids(
        self,
        obj: LeavingRequest,
    ) -> Optional[str]:
        sys_ids = obj.leaver_activitystream_user.service_now_users.all().values_list(
            "sys_id", flat=True
        )
        if not sys_ids:
            raise ValueError(
                f"Leaver {obj.leaver_activitystream_user} has no ServiceNow users"
            )
        return sys_ids

    def get_service_now_line_manager_emails(
        self,
        obj: LeavingRequest,
    ) -> Optional[str]:
        lm_emails = obj.manager_activitystream_user.service_now_users.all().values_list(
            "email", flat=True
        )
        if not lm_emails:
            raise ValueError(
                f"Leaver {obj.manager_activitystream_user} has no ServiceNow users"
            )
        return lm_emails

    def get_service_now_line_manager_user_sys_ids(
        self,
        obj: LeavingRequest,
    ) -> Optional[str]:
        lm_sys_ids = (
            obj.manager_activitystream_user.service_now_users.all().values_list(
                "sys_id", flat=True
            )
        )
        if not lm_sys_ids:
            raise ValueError(
                f"Leaver {obj.manager_activitystream_user} has no ServiceNow users"
            )
        return lm_sys_ids

    def get_service_now_users_assets(
        self,
        obj: LeavingRequest,
    ) -> Optional[List[Dict[str, str]]]:
        leaver_info = obj.leaver_information.first()
        if leaver_info.cirrus_assets:
            return [
                {
                    "asset_sys_id": asset["sys_id"],
                    "asset_tag": asset["tag"],
                    "asset_name": asset["name"],
                }
                for asset in leaver_info.cirrus_assets
            ]
        return []

    def get_service_now_additional_asset_information(
        self,
        obj: LeavingRequest,
    ) -> Optional[str]:
        leaver_info = obj.leaver_information.first()
        return leaver_info.cirrus_additional_information

    def get_service_now_collection_details(
        self,
        obj: LeavingRequest,
    ) -> Optional[Dict[str, str]]:
        leaver_info = obj.leaver_information.first()

        address_lines = []
        if leaver_info.contact_address_line_1:
            address_lines.append(leaver_info.contact_address_line_1)
        if leaver_info.contact_address_line_2:
            address_lines.append(leaver_info.contact_address_line_2)
        if leaver_info.contact_address_city:
            address_lines.append(leaver_info.contact_address_city)
        if leaver_info.contact_address_county:
            address_lines.append(leaver_info.contact_address_county)

        return {
            "contact_telephone_for_collection": leaver_info.contact_phone,
            "contact_email_for_delivery_collection": leaver_info.personal_email,
            "collection_address_for_remote_leaver": ", ".join(address_lines),
            "collection_postcode_for_remote_leaver": leaver_info.contact_address_postcode,
        }