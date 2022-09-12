from django.conf import settings

from core.lsd_zendesk.interfaces import LSDZendesk, LSDZendeskBase, LSDZendeskStubbed


def get_lsd_zendesk_interface() -> LSDZendeskBase:
    """
    Get the LSD team Zendesk interface based on the LSD_ZENDESK_LIVE
    setting being True or False.
    """
    if not settings.LSD_ZENDESK_LIVE:
        return LSDZendeskStubbed()
    return LSDZendesk()
