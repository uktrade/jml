import logging
from abc import ABC, abstractmethod
from typing import List

from core.service_now import types

logger = logging.getLogger(__name__)


class ServiceNowBase(ABC):
    @abstractmethod
    def get_active_line_managers(self) -> List[types.LineManagerDetails]:
        raise NotImplementedError

    @abstractmethod
    def get_assets_for_user(self) -> List[types.AssetDetails]:
        raise NotImplementedError
    
    @abstractmethod
    def submit_leaver_request(self, request_data: types.LeaverRequestData):
        raise NotImplementedError


class ServiceNowStubbed(ServiceNowBase):
    def get_assets_for_user(self) -> List[types.AssetDetails]:
        logger.info("Getting assets for a user")
        return [{}]

    def get_active_line_managers(self) -> List[types.LineManagerDetails]:
        logger.info("Getting active line managers")
        return [
            {
                "asset_id": "1",
                "asset_name": "Asset 1",
            },
        ]

    def submit_leaver_request(self, request_data: types.LeaverRequestData):
        logger.info("Submitting leaver request")
        logger.info(request_data)


class ServiceNowInterface(ServiceNowBase):
    def get_assets_for_user(self) -> List[types.AssetDetails]:
        return []

    def get_active_line_managers(self) -> List[types.LineManagerDetails]:
        return []

    def submit_leaver_request(self, request_data: types.LeaverRequestData):
        pass
