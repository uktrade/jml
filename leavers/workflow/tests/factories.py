from django_workflow_engine.models import Flow, TaskRecord
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from user.test.factories import UserFactory


class FlowFactory(DjangoModelFactory):
    class Meta:
        model = Flow

    workflow_name = Faker("word")
    flow_name = Faker("word")
    executed_by = SubFactory(UserFactory)


class TaskRecordFactory(DjangoModelFactory):
    class Meta:
        model = TaskRecord

    uuid = Faker("uuid4")
    flow = SubFactory(FlowFactory)
    executed_by = SubFactory(UserFactory)
    step_id = Faker("word")
    task_name = Faker("word")
    done = False
