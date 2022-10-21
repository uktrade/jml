from typing import Literal, Optional, TypedDict


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
    The Service Now API Directorate response
    """

    sys_id: str
    name: str
    u_beis_dit: Literal["", "beis", "dit"]


class ServiceNowLocation(TypedDict):
    """
    The Service Now API Location response
    """

    sys_id: str
    name: str


class ServiceNowUser(TypedDict):
    """
    The Service Now API User response
    """

    sys_id: str
    email: str
    name: str
    manager: Optional[str]


class LineManagerDetails(TypedDict):
    sys_id: str
    name: str


class DepartmentDetails(TypedDict):
    sys_id: str
    name: str


class UserDetails(TypedDict):
    sys_id: str
    email: str
    name: str
    manager: Optional[str]


class DirectorateDetails(TypedDict):
    sys_id: str
    name: str


class LocationDetails(TypedDict):
    sys_id: str
    name: str
