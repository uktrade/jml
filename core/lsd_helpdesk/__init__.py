from django.conf import settings

from core.lsd_helpdesk.interfaces import LSDHelpdesk, LSDHelpdeskBase, LSDHelpdeskStubbed


def get_lsd_helpdesk_interface() -> LSDHelpdeskBase:
    """
    Get the LSD team Helpdesk interface based on the LSD_HELP_DESK_LIVE
    setting being True or False.
    """
    if not settings.LSD_HELP_DESK_LIVE:
        return LSDHelpdeskStubbed()
    return LSDHelpdesk()
