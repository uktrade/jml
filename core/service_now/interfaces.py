from abc import ABC, abstractmethod
from typing import List, TypedDict


class AssetDetails(TypedDict):
    # TODO: Define AssetDetails
    pass


class LineManagerDetails(TypedDict):
    # TODO: Define LineManagerDetails
    pass


class LeaverRequestData(TypedDict):
    # TODO: Define LeaverRequestData
    pass


class ServiceNowBase(ABC):
    @abstractmethod
    def get_active_line_manages(self) -> List[LineManagerDetails]:
        raise NotImplementedError

    @abstractmethod
    def get_assets_for_user(self) -> List[AssetDetails]:
        raise NotImplementedError
    
    @abstractmethod
    def submit_leaver_request(self, request_data: LeaverRequestData):
        raise NotImplementedError


class ServiceNowStubbed(ServiceNowBase):
    def get_assets_for_user(self) -> List[AssetDetails]:
        return []

    def get_active_line_manages(self) -> List[LineManagerDetails]:
        return []

    def submit_leaver_request(self, request_data: LeaverRequestData):
        pass


class ServiceNowInterface(ServiceNowBase):
    def get_assets_for_user(self) -> List[AssetDetails]:
        return []

    def get_active_line_manages(self) -> List[LineManagerDetails]:
        return []

    def submit_leaver_request(self, request_data: LeaverRequestData):
        pass
