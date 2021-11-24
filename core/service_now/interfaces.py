import logging
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional, TypedDict

logger = logging.getLogger(__name__)


class AssetDetails(TypedDict):
    # TODO: Define AssetDetails
    pass


class LineManagerDetails(TypedDict):
    # TODO: Define LineManagerDetails
    pass


class Address(TypedDict):
    # Note: This is based on https://design-system.service.gov.uk/patterns/addresses/multiple/index.html
    # We can alter this based on what data we take from the form and how
    # Service Now expects the data.
    building_and_street: str
    city: str
    county: str
    postcode: str


class LeaverRequestData(TypedDict):
    collection_address: Optional[Address]
    collection_telephone: Optional[str]
    collection_email: str
    reason_for_leaving: str
    leaving_date: date
    employee_email: str
    employee_name: str
    employee_department: str
    employee_directorate: str
    employee_staff_id: str
    manager_name: str
    assets: List[AssetDetails]
    assets_confirmation: bool
    assets_information: str


class ServiceNowBase(ABC):
    @abstractmethod
    def get_active_line_managers(self) -> List[LineManagerDetails]:
        raise NotImplementedError

    @abstractmethod
    def get_assets_for_user(self) -> List[AssetDetails]:
        raise NotImplementedError
    
    @abstractmethod
    def submit_leaver_request(self, request_data: LeaverRequestData):
        raise NotImplementedError


class ServiceNowStubbed(ServiceNowBase):
    def get_assets_for_user(self) -> List[AssetDetails]:
        logger.info("Getting assets for a user")
        return []

    def get_active_line_managers(self) -> List[LineManagerDetails]:
        logger.info("Getting active line managers")
        return []

    def submit_leaver_request(self, request_data: LeaverRequestData):
        logger.info("Submitting leaver request")
        logger.info(request_data)


class ServiceNowInterface(ServiceNowBase):
    def get_assets_for_user(self) -> List[AssetDetails]:
        return []

    def get_active_line_managers(self) -> List[LineManagerDetails]:
        return []

    def submit_leaver_request(self, request_data: LeaverRequestData):
        pass
