from django.conf import settings
from django.http.request import HttpRequest
from django.utils.module_loading import import_string

from core.staff_sso.interfaces import StaffSSOBase, StaffSSOStubbed


def get_staff_sso_interface(*, request: HttpRequest) -> StaffSSOBase:
    """
    Get the SSO interface from the STAFF_SSO_INTERFACE setting
    """
    if not settings.STAFF_SSO_INTERFACE:
        return StaffSSOStubbed(request=request)

    interface_class = import_string(settings.STAFF_SSO_INTERFACE)
    if not issubclass(interface_class, StaffSSOBase):
        raise ValueError("STAFF_SSO_INTERFACE must inherit from StaffSSOBase")

    return interface_class(request=request)
