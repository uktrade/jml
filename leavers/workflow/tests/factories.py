from django_workflow_engine.models import Flow, TaskStatus
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from user.test.factories import UserFactory


class FlowFactory(DjangoModelFactory):
    class Meta:
        model = Flow

    workflow_name = Faker("word")
    flow_name = Faker("word")
    executed_by = SubFactory(UserFactory)


class TaskStatusFactory(DjangoModelFactory):
    class Meta:
        model = TaskStatus

    uuid = Faker("uuid4")
    flow = SubFactory(FlowFactory)
    executed_by = SubFactory(UserFactory)
    step_id = Faker("word")
    task_name = Faker("word")
    done = False
