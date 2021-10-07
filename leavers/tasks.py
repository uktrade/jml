from django_workflow_engine import (
    Task,
    TaskError,
)

from leavers.forms import LeaversForm
from leavers.models import LeavingRequest


class SetupLeaving(Task, input="setup_leaving"):  # type: ignore
    auto = True

    def execute(self, task_info):
        LeavingRequest.objects.create(flow=self.flow)

        return None, {}


class CreateLeavingRequest(Task, input="create_leaving_request"):  # type: ignore
    auto = False
    form_class = LeaversForm
    template = "flow_continue.html"

    def execute(self, task_info):
        form = self.form_class(instance=self.flow.leaving_request, data=task_info)

        if form.is_valid():
            form.save()
        else:
            raise TaskError("Form is not valid", {"form": form})

        return None, form.cleaned_data

    def context(self):
        return {"form": self.form_class(instance=self.flow.leaving_request)}
