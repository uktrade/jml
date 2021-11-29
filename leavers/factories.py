import uuid

import factory
from factory.django import DjangoModelFactory

from leavers import models
from user.test.factories import UserFactory


class LeavingRequestFactory(DjangoModelFactory):
    class Meta:
        model = models.LeavingRequest

    uuid = uuid.uuid4()
    user_requesting = factory.SubFactory(UserFactory)


class LeaverUpdatesFactory(DjangoModelFactory):
    class Meta:
        model = models.LeaverUpdates

    leaver_email = factory.Faker("email")
    updates = {}
