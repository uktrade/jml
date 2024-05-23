import factory
from factory.django import DjangoModelFactory

from core.beis_service_now.models import (
    ServiceNowDirectorate,
    ServiceNowLocation,
    ServiceNowObject,
)


class ServiceNowObjectFactory(DjangoModelFactory):
    class Meta:
        model = ServiceNowObject

    sys_id = factory.Sequence(lambda n: f"sys_id_{n}")


class ServiceNowDirectorateFactory(ServiceNowObjectFactory):
    class Meta:
        model = ServiceNowDirectorate

    name = factory.Sequence(lambda n: f"Directorate {n}")


class ServiceNowLocationFactory(ServiceNowObjectFactory):
    class Meta:
        model = ServiceNowLocation

    name = factory.Sequence(lambda n: f"Location {n}")
