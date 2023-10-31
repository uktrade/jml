from pydantic import BaseModel


class ServiceNowPostObject(BaseModel):
    ...


class ServiceNowPostAsset(ServiceNowPostObject):
    """
    Example data:
    ```JSON
    {
        "asset_sys_id": "00000a000bc000000000de00000fgh0i", # /PS-IGNORE
        "model_category": "Computer",
        "model": "Apple Mac14,2",
        "display_name": "EUDS00123 - Apple Mac14,2",
        "install_status": "In use",
        "substatus": "",
        "assigned_to_sys_id": "000a00000b00c0000000de00000fgh0i",
        "assigned_to_display_name": "DBT user TEST",
        "asset_tag": "EUDS00123",
        "serial_number": "SER12NUM3" # /PS-IGNORE
    }
    ```
    """

    asset_sys_id: str
    model_category: str
    model: str
    display_name: str
    install_status: str
    substatus: str
    assigned_to_sys_id: str
    assigned_to_display_name: str
    asset_tag: str
    serial_number: str


class ServiceNowPostUser(ServiceNowPostObject):
    """
    Example data:
    ```JSON
    {
        "user_sys_id": "0000a0000bcde000f00g0000h0ijk0l", # /PS-IGNORE
        "user_name": "JohnS@trade.gov.uk", # /PS-IGNORE
        "name": "John Smith",
        "email": "John.Smith@trade.gov.uk", # /PS-IGNORE
        "manager_user_name": "Jane Doe",
        "manager_sys_id": "00000000ab0c0d00000ef0g00h0000ij"
    }
    ```
    """

    user_sys_id: str
    user_name: str
    name: str
    email: str
    manager_user_name: str
    manager_sys_id: str


class ServiceNowPostDirectorate(ServiceNowPostObject):
    """
    Example data:
    ```JSON
    {
        "directorate_sys_id": "00a000b00cd0e0000000fg00000hij00", # /PS-IGNORE
        "name": "Directorate name"
    }
    ```
    """

    directorate_sys_id: str
    name: str
