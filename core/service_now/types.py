
from datetime import date
from typing import List, Optional, TypedDict


class AssetDetails(TypedDict):
    # TODO: Alter this based on the data the Service Now API expects.
    asset_id: Optional[str]
    asset_name: str


class LineManagerDetails(TypedDict):
    # TODO: Define LineManagerDetails based on Service Now API response.
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