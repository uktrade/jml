from typing import List, TypedDict


class ServiceNowPostObject(TypedDict):
    sys_id: str


class ServiceNowPostAsset(ServiceNowPostObject):
    model_category: str
    model: str
    display_name: str
    install_status: str
    substatus: str
    assigned_to: str
    asset_tag: str
    serial_number: str


ServiceNowAssetPostBody = List[ServiceNowPostAsset]


class ServiceNowPostUser(ServiceNowPostObject):
    ...


ServiceNowUserPostBody = List[ServiceNowPostUser]


class ServiceNowPostDirectorate(ServiceNowPostObject):
    ...


ServiceNowDirectoratePostBody = List[ServiceNowPostDirectorate]
