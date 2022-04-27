from django.conf import settings
from django.utils.module_loading import import_string

from core.uksbs.interfaces import UKSBSBase, UKSBSStubbed


def get_uksbs_interface() -> UKSBSBase:
    """
    Get the UK SBS interface from the UK_SBS_INTERFACE setting
    """
    if not settings.UK_SBS_INTERFACE:
        return UKSBSStubbed()

    interface_class = import_string(settings.UK_SBS_INTERFACE)
    if not issubclass(interface_class, UKSBSBase):
        raise ValueError("UK_SBS_INTERFACE must inherit from UKSBSBase")

    return interface_class()
