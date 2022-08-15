import json
import logging
from abc import ABC, abstractmethod
from random import choice
from typing import TYPE_CHECKING, Iterable, List, Optional

from django.conf import settings
from django.core.cache import cache

from activity_stream.models import ActivityStreamStaffSSOUser
from core.service_now import types
from core.service_now.client import ServiceNowClient
from core.utils.helpers import bool_to_yes_no
from core.utils.staff_index import StaffDocument, get_staff_document_from_staff_index
from leavers import types as leavers_types

if TYPE_CHECKING:
    from leavers.models import LeaverInformation, LeavingRequest

logger = logging.getLogger(__name__)


class ServiceNowUserNotFound(Exception):
    pass


class ServiceNowBase(ABC):
    @abstractmethod
    def get_asset_by_tag(self, asset_tag: str) -> types.AssetDetails:
        raise NotImplementedError

    @abstractmethod
    def get_assets_for_user(self, email: str) -> List[types.AssetDetails]:
        raise NotImplementedError

    @abstractmethod
    def get_users(self, email: str) -> List[types.UserDetails]:
        raise NotImplementedError

    @abstractmethod
    def get_user(self, email: str) -> types.UserDetails:
        raise NotImplementedError

    @abstractmethod
    def get_departments(
        self, sys_id: Optional[str] = None
    ) -> List[types.DepartmentDetails]:
        raise NotImplementedError

    @abstractmethod
    def get_directorates(
        self, sys_id: Optional[str] = None, name: Optional[str] = None
    ) -> List[types.DirectorateDetails]:
        raise NotImplementedError

    @abstractmethod
    def submit_leaver_request(
        self,
        leaver_info: "LeaverInformation",
        leaver_details: leavers_types.LeaverDetails,
        assets: List[types.AssetDetails],
    ):
        raise NotImplementedError


class ServiceNowStubbed(ServiceNowBase):
    def get_asset_by_tag(self, asset_tag: str) -> types.AssetDetails:
        logger.info(f"Getting an asset with the tag {asset_tag}")
        return {
            "sys_id": "111",
            "tag": asset_tag,
            "name": "Asset 1",
        }

    def get_assets_for_user(self, email: str) -> List[types.AssetDetails]:
        logger.info("Getting assets for a user")
        assets: List[types.AssetDetails] = []

        asset_count = choice([0, 1, 2])

        while len(assets) < asset_count:
            i = len(assets) + 1
            assets.append(
                {
                    "sys_id": f"sys_id_{i}",
                    "tag": f"asset_tag_{i}",
                    "name": f"Asset {i}",
                }
            )

        return assets

    def get_users(self, email: str) -> List[types.UserDetails]:
        logger.info("Getting users")
        return [
            {
                "sys_id": "1",
                "name": "User 1",
                "email": "manager1@example.com",  # /PS-IGNORE
                "manager": "manager1@example.com",  # /PS-IGNORE
            }
        ]

    def get_user(self, email: str) -> types.UserDetails:
        logger.info("Getting user")
        users = self.get_users(email=email)
        for user in users:
            if user["email"] == email:
                return user
        raise ServiceNowUserNotFound()

    def get_departments(
        self, sys_id: Optional[str] = None
    ) -> List[types.DepartmentDetails]:
        logger.info("Getting departments")
        test_departments: List[types.DepartmentDetails] = [
            {"sys_id": "1", "name": "Department 1"},
            {"sys_id": "2", "name": "Department 2"},
            {
                "sys_id": settings.SERVICE_NOW_DIT_DEPARTMENT_SYS_ID,
                "name": "Department of International Trade",
            },
        ]
        if sys_id:
            filtered_result: List[types.DepartmentDetails] = []
            for test_department in test_departments:
                if test_department["sys_id"] == sys_id:
                    filtered_result.append(test_department)
                    break
            return filtered_result
        return test_departments

    def get_directorates(
        self, sys_id: Optional[str] = None, name: Optional[str] = None
    ) -> List[types.DirectorateDetails]:
        logger.info("Getting directorates")
        test_directorates: List[types.DirectorateDetails] = [
            {"sys_id": "1", "name": "Directorate 1"},
            {"sys_id": "2", "name": "Directorate 2"},
        ]
        if sys_id:
            for test_directorate in test_directorates:
                if test_directorate["sys_id"] == sys_id:
                    return [test_directorate]
        return test_directorates

    def submit_leaver_request(
        self,
        leaver_info: "LeaverInformation",
        leaver_details: leavers_types.LeaverDetails,
        assets: List[types.AssetDetails],
    ):
        logger.info("Submitting leaver request")
        logger.info(leaver_info)
        logger.info(leaver_details)
        logger.info(assets)


class AssetNotFound(Exception):
    pass


class TooManyAssetsReturned(Exception):
    pass


class ServiceNowInterface(ServiceNowBase):
    def __init__(self, *args, **kwargs):
        self.GET_USER_PATH = settings.SERVICE_NOW_GET_USER_PATH
        self.GET_ASSET_PATH = settings.SERVICE_NOW_GET_ASSET_PATH
        self.GET_DIRECTORATE_PATH = settings.SERVICE_NOW_GET_DIRECTORATE_PATH
        self.POST_LEAVER_REQUEST = settings.SERVICE_NOW_POST_LEAVER_REQUEST
        self.client = ServiceNowClient()

    def get_asset_by_tag(self, asset_tag: str) -> types.AssetDetails:
        # Check if there is a cached result
        cache_key: str = f"asset_{asset_tag}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        # Get all data from Service Now /PS-IGNORE
        service_now_assets: Iterable[types.ServiceNowAsset] = self.client.get_results(
            path=self.GET_ASSET_PATH,
            sysparm_query=f"asset_tag={asset_tag}",
            sysparm_fields=[
                "sys_id",
                "asset_tag",
                "display_name",
            ],
        )
        # Convert to a list of AssetDetails
        asset_details: List[types.AssetDetails] = [
            {
                "sys_id": service_now_asset["sys_id"],
                "tag": service_now_asset["asset_tag"],
                "name": service_now_asset["display_name"],
            }
            for service_now_asset in service_now_assets
        ]

        asset_count = len(asset_details)

        if asset_count == 0:
            raise AssetNotFound
        if asset_count != 1:
            raise TooManyAssetsReturned

        asset_detail: types.AssetDetails = asset_details[0]

        # Store the result in the cache
        cache.set(cache_key, asset_detail)
        return asset_detail

    def get_assets_for_user(self, email: str) -> List[types.AssetDetails]:
        # Check if there is a cached result
        cache_key: str = f"assets_for_user_{email}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        # Get all data from Service Now /PS-IGNORE
        service_now_assets: Iterable[types.ServiceNowAsset] = self.client.get_results(
            path=self.GET_ASSET_PATH,
            sysparm_query=f"assigned_to.email={email}",
            sysparm_fields=[
                "sys_id",
                "asset_tag",
                "display_name",
            ],
        )
        # Convert to a list of AssetDetails
        asset_details: List[types.AssetDetails] = [
            {
                "sys_id": service_now_asset["sys_id"],
                "tag": service_now_asset["asset_tag"],
                "name": service_now_asset["display_name"],
            }
            for service_now_asset in service_now_assets
        ]

        # Store the result in the cache
        cache.set(cache_key, asset_details)
        return asset_details

    def get_users(self, email: str) -> List[types.UserDetails]:
        # Check if there is a cached result
        cache_key: str = f"get_users_{email}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        # Get all data from Service Now /PS-IGNORE
        service_now_users: Iterable[types.ServiceNowUser] = self.client.get_results(
            path=self.GET_USER_PATH,
            sysparm_query=f"email={email}",
            sysparm_fields=[
                "sys_id",
                "name",
                "email",
                "manager",
            ],
        )
        # Convert to a list of UserDetails /PS-IGNORE
        users_details: List[types.UserDetails] = []
        for service_now_user in service_now_users:
            logger.info(f"Service Now user found '{service_now_user}'")
            user_details: types.UserDetails = {
                "sys_id": service_now_user["sys_id"],
                "name": service_now_user["name"],
                "email": str(service_now_user["email"]).lower(),
                "manager": service_now_user.get("manager"),
            }
            users_details.append(user_details)

        # Store the result in the cache
        cache.set(cache_key, users_details)
        return users_details

    def get_user(self, email: str) -> types.UserDetails:
        users = self.get_users(email=email)
        for user in users:
            if user["email"] == email:
                return user
        raise ServiceNowUserNotFound()

    def get_departments(
        self, sys_id: Optional[str] = None
    ) -> List[types.DepartmentDetails]:
        # Check if there is a cached result
        cache_key: str = f"get_departments_{sys_id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        results: List[types.DepartmentDetails] = [
            {
                "sys_id": settings.SERVICE_NOW_DIT_DEPARTMENT_SYS_ID,
                "name": "Department of International Trade",
            }
        ]

        if sys_id:
            filtered_result: List[types.DepartmentDetails] = []
            for result in results:
                if result["sys_id"] == sys_id:
                    filtered_result.append(result)
                    break
            # Store the result in the cache
            cache.set(cache_key, filtered_result)
            return filtered_result

        # Store the result in the cache
        cache.set(cache_key, results)
        return results

    def get_directorates(
        self, sys_id: Optional[str] = None, name: Optional[str] = None
    ) -> List[types.DirectorateDetails]:
        # Check if there is a cached result
        cache_key: str = f"get_directorates{sys_id}_{name}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        query = ""
        if sys_id:
            query = f"sys_id={sys_id}"
        if name:
            query = f"name={name}"

        # Get all data from Service Now /PS-IGNORE
        service_now_directorates: Iterable[
            types.ServiceNowDirectorate
        ] = self.client.get_results(
            path=self.GET_DIRECTORATE_PATH,
            sysparm_query=query,
            sysparm_fields=[
                "sys_id",
                "name",
            ],
        )
        # Convert to a list of DirectorateDetails /PS-IGNORE
        directorate_details: List[types.DirectorateDetails] = [
            {
                "sys_id": service_now_directorate["sys_id"],
                "name": service_now_directorate["name"],
            }
            for service_now_directorate in service_now_directorates
        ]

        # Store the result in the cache
        cache.set(cache_key, directorate_details)
        return directorate_details

    def submit_leaver_request(
        self,
        leaver_info: "LeaverInformation",
        leaver_details: leavers_types.LeaverDetails,
        assets: List[types.AssetDetails],
    ):
        if not settings.PROCESS_LEAVING_REQUEST:
            full_name = leaver_details["first_name"] + " " + leaver_details["last_name"]
            logger.warning(f"Submitting leaver request to Service Now for {full_name}")
            return None

        leaving_request: "LeavingRequest" = leaver_info.leaving_request

        leaver_email = leaving_request.get_leaver_email()
        if not leaver_email:
            raise Exception("Unable to get leaver's email")

        # Convert Request Data to what the Service Now API expects
        assets_confirmation = bool_to_yes_no(leaver_info.information_is_correct).title()

        leaving_date: str = ""
        if leaver_info.leaving_date:
            leaving_date = leaver_info.leaving_date.strftime("%d/%m/%Y")

        collection_address = leaver_info.return_address
        collection_address_str: str = ""
        if collection_address["line_1"]:
            collection_address_str += collection_address["line_1"] + "\n"
        if collection_address["line_2"]:
            collection_address_str += collection_address["line_2"] + "\n"
        if collection_address["town_or_city"]:
            collection_address_str += collection_address["town_or_city"] + "\n"
        if collection_address["county"]:
            collection_address_str += collection_address["county"]

        leaver: Optional[
            ActivityStreamStaffSSOUser
        ] = leaving_request.leaver_activitystream_user
        if not leaver:
            raise Exception("Unable to get leaver information")
        leaver_staff_document: StaffDocument = get_staff_document_from_staff_index(
            sso_email_user_id=leaver.email_user_id,
        )
        leaver_service_now_id = leaver_staff_document.service_now_user_id

        processing_manager: Optional[
            ActivityStreamStaffSSOUser
        ] = leaving_request.processing_manager_activitystream_user
        if not processing_manager:
            raise Exception("Unable to get Line Manager information")

        manager_staff_document: StaffDocument = get_staff_document_from_staff_index(
            sso_email_user_id=processing_manager.email_user_id,
        )
        manager_service_now_id = manager_staff_document.service_now_user_id

        service_now_request_data = {
            "sysparm_quantity": "1",
            "variables": {
                "leaver_staff_id": leaver_details["staff_id"],
                "leaver_leave_date": leaving_date,
                "assets_confirmation": assets_confirmation,
                "Additional_information": leaver_info.additional_information,
                "contact_telephone_for_collection": leaver_info.return_personal_phone,
                "contact_email_for_delivery_collection": leaver_info.return_contact_email,  # noqa E501
                "collection_address_for_remote_leaver": collection_address_str,
                "collection_postcode_for_remote_leaver": collection_address["postcode"],
                "leaver_user": leaver_service_now_id,
                "users_manager": manager_service_now_id,
                "leaver_other_reason": "",
                "leaver_dept": settings.SERVICE_NOW_DIT_DEPARTMENT_SYS_ID,
                "u_users_directorate": "",
                "users_assets": json.dumps(
                    [
                        {
                            "asset_tag": asset_details["tag"],
                            "asset_name": asset_details["name"],
                        }
                        for asset_details in assets
                    ]
                ),
                "leaver_email": leaver_email,
            },
            "get_portal_messages": "true",
            "sysparm_no_validation": "true",
        }
        # Submit the leaver request
        response = self.client.post(
            self.POST_LEAVER_REQUEST, json=service_now_request_data
        )

        return response
