from django.conf import settings

from core.lsd_help_desk.interfaces import (
    LSDHelpDesk,
    LSDHelpDeskBase,
    LSDHelpDeskStubbed,
)


def get_lsd_help_desk_interface() -> LSDHelpDeskBase:
    """
    Get the LSD team help desk interface based on the LSD_HELP_DESK_LIVE
    setting being True or False.
    """
    if not settings.LSD_HELP_DESK_LIVE:
        return LSDHelpDeskStubbed()
    return LSDHelpDesk()
