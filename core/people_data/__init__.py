from django.conf import settings
from django.utils.module_loading import import_string

from core.people_data.interfaces import PeopleDataBase, PeopleDataStubbed


def get_people_data_interface() -> PeopleDataBase:
    """
    Get the People Data report interface from the PEOPLE_DATA_INTERFACE setting
    """
    if not getattr(settings, "PEOPLE_DATA_INTERFACE", None):
        return PeopleDataStubbed()

    interface_class = import_string(settings.PEOPLE_DATA_INTERFACE)
    if not issubclass(interface_class, PeopleDataBase):
        raise ValueError("PEOPLE_DATA_INTERFACE must inherit from PeopleDataBase")

    return interface_class()
