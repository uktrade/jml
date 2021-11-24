from django.conf import settings
from django.utils.module_loading import import_string

from core.service_now.interfaces import ServiceNowBase, ServiceNowStubbed


def get_service_now_interface() -> ServiceNowBase:
    """
    Get the Service Now interface from the SERVICE_NOW_INTERFACE setting
    """
    if not settings.SERVICE_NOW_INTERFACE:
        return ServiceNowStubbed()

    interface_class = import_string(settings.SERVICE_NOW_INTERFACE)
    if not issubclass(ServiceNowBase, interface_class):
        raise ValueError("SERVICE_NOW_INTERFACE must inherit from ServiceNowBase")

    return interface_class()
