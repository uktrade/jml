import logging
from abc import ABC, abstractmethod
from typing import List, Literal
from urllib.parse import urlencode, urlparse, urlunparse

import requests
from django.conf import settings

from core.service_now import types
from leavers import types as leavers_types
from leavers.models import LeaverInformation

logger = logging.getLogger(__name__)


class ServiceNowBase(ABC):
    @abstractmethod
    def get_assets_for_user(self, email: str) -> List[types.AssetDetails]:
        raise NotImplementedError

    @abstractmethod
    def get_active_line_managers(self) -> List[types.LineManagerDetails]:
        raise NotImplementedError

    @abstractmethod
    def get_departments(self) -> List[types.DepartmentDetails]:
        raise NotImplementedError

    @abstractmethod
    def get_directorates(self) -> List[types.DirectorateDetails]:
        raise NotImplementedError

    @abstractmethod
    def submit_leaver_request(
        self,
        leaver_info: LeaverInformation,
        leaver_details: leavers_types.LeaverDetails,
        assets: List[types.AssetDetails],
    ):
        raise NotImplementedError


class ServiceNowStubbed(ServiceNowBase):
    def get_assets_for_user(self, email: str) -> List[types.AssetDetails]:
        logger.info("Getting assets for a user")
        return [
            {
                "sys_id": "111",
                "tag": "1",
                "name": "Asset 1",
            },
        ]

    def get_active_line_managers(self) -> List[types.LineManagerDetails]:
        logger.info("Getting active line managers")
        return [
            {
                "sys_id": "222",
                "name": "Line Manager 1",
            }
        ]

    def get_departments(self) -> List[types.DepartmentDetails]:
        logger.info("Getting departments")
        return [{"sys_id": "1", "name": "Department 1"}]

    def get_directorates(self) -> List[types.DirectorateDetails]:
        logger.info("Getting directorates")
        return [{"sys_id": "1", "name": "Directorate 1"}]

    def submit_leaver_request(
        self,
        leaver_info: LeaverInformation,
        leaver_details: leavers_types.LeaverDetails,
        assets: List[types.AssetDetails],
    ):
        logger.info("Submitting leaver request")
        logger.info(leaver_info)
        logger.info(leaver_details)
        logger.info(assets)


class ServiceNowInterface(ServiceNowBase):

    GET_ASSET_PATH = settings.SERVICE_NOW_GET_ASSET_PATH
    POST_LEAVER_REQUEST = settings.SERVICE_NOW_POST_LEAVER_REQUEST

    def __init__(self, *args, **kwargs):
        if not settings.SERVICE_NOW_API_URL:
            raise ValueError("SERVICE_NOW_API_URL is not set")
        self.service_now_api_url = settings.SERVICE_NOW_API_URL

    def get_assets_for_user(self, email: str) -> List[types.AssetDetails]:
        # Build the URL
        get_assets_url = f"{self.service_now_api_url}{self.GET_ASSET_PATH}"
        url_parts = list(urlparse(get_assets_url))
        query = {
            "sysparm_fields": "sys_id,asset_tag,display_name",
            "sysparm_query": f"assigned_to.email={email}",
        }
        url_parts[4] = urlencode(query)
        query_url = urlunparse(url_parts)

        # Make the request for the asset list
        response = requests.get(query_url)
        if response.status_code != 200:
            raise Exception("Failed to get assets for user")
        content = response.json()
        service_now_assets: List[types.ServiceNowAsset] = content.get("result", [])

        # Convert to a list of AssetDetails
        asset_details: List[types.AssetDetails] = [
            {
                "sys_id": service_now_asset["sys_id"],
                "tag": service_now_asset["asset_tag"],
                "name": service_now_asset["display_name"],
            }
            for service_now_asset in service_now_assets
        ]

        return asset_details

    def get_active_line_managers(self) -> List[types.LineManagerDetails]:
        return []

    def get_departments(self) -> List[types.DepartmentDetails]:
        return []

    def get_directorates(self) -> List[types.DirectorateDetails]:
        return []

    def submit_leaver_request(
        self,
        leaver_info: LeaverInformation,
        leaver_details: leavers_types.LeaverDetails,
        assets: List[types.AssetDetails],
    ):
        # Convert Request Data to what the Service Now API expects
        assets_confirmation: Literal["Yes", "No"] = "No"
        if leaver_info.information_is_correct:
            assets_confirmation = "Yes"

        leaving_date: str = ""
        if leaver_info.leaving_date:
            leaving_date = leaver_info.leaving_date.strftime("%d/%m/%Y")

        collection_address: types.Address = {
            "building_and_street": leaver_info.return_address_building_and_street or "",
            "city": leaver_info.return_address_city or "",
            "county": leaver_info.return_address_county or "",
            "postcode": leaver_info.return_address_postcode or "",
        }

        service_now_request_data = {
            "sysparm_quantity": "1",
            "variables": {
                "leaver_staff_id": leaver_details["staff_id"],
                "leaver_leave_date": leaving_date,
                "assets_confirmation": assets_confirmation,
                "Additional_information": leaver_info.additional_information,
                "contact_telephone_for_collection": leaver_info.return_personal_phone,
                "contact_email_for_delivery_collection": leaver_info.return_contact_email,  # noqa E501
                "collection_address_for_remote_leaver": (
                    f"{collection_address['building_and_street']}\n"
                    f"{collection_address['city']}\n"
                    f"{collection_address['county']}"
                ),
                "collection_postcode_for_remote_leaver": collection_address["postcode"],
                "leaver_user": "",
                "users_manager": leaver_details["manager"],
                "leaver_other_reason": "",
                "leaver_dept": leaver_details["department"],
                "u_users_directorate": leaver_details["directorate"],
                "users_assets": [
                    {
                        "asset_tag": asset_details["tag"],
                        "asset_name": asset_details["name"],
                    }
                    for asset_details in assets
                ],
                "leaver_email": leaver_info.leaver_email,
            },
            "get_portal_messages": "true",
            "sysparm_no_validation": "true",
        }
        # Submit the leaver request
        response = requests.post(
            self.POST_LEAVER_REQUEST, json=service_now_request_data
        )

        return response
