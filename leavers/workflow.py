from django_workflow_engine import Workflow, Step, Task, TaskError
from django import forms

from leavers.models import LeavingRequest

from leavers.tasks import (
    SetupLeaving,
    CreateLeavingRequest,
)


LeaversWorkflow = Workflow(
    name="leaving",
    steps=[
        Step(
            step_id="setup_leaving",
            task_name="setup_leaving",
            start=True,
            target="create_leaving_request",
        ),
        Step(
            step_id="create_leaving_request",
            task_name="create_leaving_request",
            target=None,
        ),
    ],
)
