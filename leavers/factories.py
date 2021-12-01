import uuid

import factory
from factory.django import DjangoModelFactory

from leavers import models, types
from user.test.factories import UserFactory


class LeavingRequestFactory(DjangoModelFactory):
    class Meta:
        model = models.LeavingRequest

    uuid = uuid.uuid4()
    user_requesting = factory.SubFactory(UserFactory)


class LeaverInformationFactory(DjangoModelFactory):
    class Meta:
        model = models.LeaverInformation

    leaver_email = factory.Faker("email")
    updates: types.LeaverDetailUpdates = {}
