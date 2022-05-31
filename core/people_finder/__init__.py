from django.conf import settings
from django.utils.module_loading import import_string

from core.people_finder.interfaces import PeopleFinderBase, PeopleFinderStubbed


def get_people_finder_interface() -> PeopleFinderBase:
    """
    Get the People Finder interface from the PEOPLE_FINDER_INTERFACE setting
    """
    if not getattr(settings, "PEOPLE_FINDER_INTERFACE", None):
        return PeopleFinderStubbed()

    interface_class = import_string(settings.PEOPLE_FINDER_INTERFACE)
    if not issubclass(interface_class, PeopleFinderBase):
        raise ValueError("PEOPLE_FINDER_INTERFACE must inherit from PeopleFinderBase")

    return interface_class()
