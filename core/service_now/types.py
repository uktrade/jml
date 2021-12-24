from typing import Optional, TypedDict


class AssetDetails(TypedDict):
    """
    The Asset's details stored in the application and reported back to Service Now
    """

    sys_id: Optional[str]
    tag: Optional[str]
    name: str


class ServiceNowAsset(TypedDict):
    """
    The Service Now API Asset response
    """

    sys_id: str
    asset_tag: str
    display_name: str


class ServiceNowDirectorate(TypedDict):
    """
    The Service Now API Directorate response /PS-IGNORE
    """

    sys_id: str
    name: str


class ServiceNowUser(TypedDict):
    """
    The Service Now API User response
    """

    sys_id: str
    name: str
    manager: Optional[str]


class LineManagerDetails(TypedDict):
    sys_id: str
    name: str


class Address(TypedDict):
    # See: https://design-system.service.gov.uk/patterns/addresses/multiple/index.html
    # We can alter this based on what data we take from the form and how
    # Service Now expects the data.
    building_and_street: str
    city: str
    county: str
    postcode: str


class DepartmentDetails(TypedDict):
    sys_id: str
    name: str


class UserDetails(TypedDict):
    sys_id: str
    name: str
    manager: Optional[str]


class DirectorateDetails(TypedDict):
    sys_id: str
    name: str
