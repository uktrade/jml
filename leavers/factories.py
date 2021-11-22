import uuid
import factory
from factory.django import DjangoModelFactory

from leavers.models import LeavingRequest
from user.test.factories import UserFactory


class LeavingRequestFactory(DjangoModelFactory):
    class Meta:
        model = LeavingRequest
    
    uuid =  uuid.uuid4()
    user_requesting = factory.SubFactory(UserFactory)
