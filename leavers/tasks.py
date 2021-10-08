from django.contrib.auth import get_user_model

from django_workflow_engine import (
    Task,
    TaskError,
)

from leavers.forms import (
    LeaversForm,
    HardwareReceivedForm,
)
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


class FindGroupRecipients(Task, input="find_group_recipients"):
    auto = True

    def execute(self, task_info):
        User = get_user_model()
        users = User.objects.filter(
            groups__name=self.task_record.task_info["group_name"]
        )

        return None, {"recipient_list": list(users.values_list("email"))}


class ConfirmHardwareReceived(Task, input="confirm_hardware_received"):
    auto = False
    form_class = HardwareReceivedForm
    template = "confirm_hardware_received.html"

    def execute(self, task_info):
        form = self.form_class(instance=self.flow.leaving_request, data=task_info)

        if not form.is_valid():
            # TODO: how to display form with errors
            raise TaskError("Form is not valid", {"form": form})

        target = "hardware_approved"

        return target, form.cleaned_data

    def context(self):
        return {"form": self.form_class(instance=self.flow.leaving_request)}
