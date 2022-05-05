from django.conf import settings
from django.utils.module_loading import import_string

from core.uksbs.interfaces import UKSBSBase, UKSBSStubbed


def get_uksbs_interface() -> UKSBSBase:
    """
    Get the UK SBS interface from the UKSBS_INTERFACE setting
    """
    if not settings.UKSBS_INTERFACE:
        return UKSBSStubbed()

    interface_class = import_string(settings.UKSBS_INTERFACE)
    if not issubclass(interface_class, UKSBSBase):
        raise ValueError("UKSBS_INTERFACE must inherit from UKSBSBase")

    return interface_class()
