from django.contrib.auth import get_user_model
from django.views.generic.edit import FormView
from django_workflow_engine import (
    Task,
    TaskError,
)

from core.utils.slack import send_slack_message

from leavers.forms import (
    LeaversForm,
    HardwareReceivedForm,
    SREConfirmCompleteForm,
)
from leavers.models import LeavingRequest


class SetupLeaving(Task, input="setup_leaving"):  # type: ignore
    auto = True

    def execute(self, task_info):


        return None, {}
#
#
# class CreateLeavingRequest(Task, input="create_leaving_request"):  # type: ignore
#     auto = False
#     form_class = LeaversForm
#     template = "flow/flow_continue.html"
#
#     def execute(self, task_info):
#         form = self.form_class(data=task_info)
#
#         if form.is_valid():
#             self.flow.leaving_request.last_day = form.cleaned_data["last_day"]
#             if form.cleaned_data["for_self"]:
#                 self.flow.leaving_request.leaver_user = self.user
#             else:
#                 self.flow.leaving_request.requester_user = self.user
#             self.flow.leaving_request.save()
#         else:
#             raise TaskError("Form is not valid", {"form": form})
#
#         return None, form.cleaned_data
#
#     def context(self):
#         return {"form": self.form_class()}


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
    template = "flow/basic_form.html"

    def execute(self, task_info):
        form = self.form_class(instance=self.flow.leaving_request, data=task_info)

        if not form.is_valid():
            # TODO: how to display form with errors
            raise TaskError("Form is not valid", {"form": form})

        target = "hardware_approved"

        return target, form.cleaned_data

    def context(self):
        return {"form": self.form_class(instance=self.flow.leaving_request)}


class SREEConfirmTasksComplete(Task, input="sre_confirm_tasks_complete"):
    auto = False
    form_class = SREConfirmCompleteForm
    template = "flow/basic_form.html"

    def execute(self, task_info):
        form = self.form_class(data=task_info)

        if not form.is_valid():
            raise TaskError("Form is not valid", {"form": form})

        target = "sre_tasks_complete"

        return target, form.cleaned_data

    def context(self):
        return {"form": self.form_class()}

#
# class SREEConfirmTasksComplete(Task, input="sre_confirm_tasks_complete"):
#     auto = False
#     form_class = ""  # TODO own form
#     template = ""  # TODO own template
#
#     def execute(self, task_info):
#         form = self.form_class(instance=self.flow.leaving_request, data=task_info)
#
#         if not form.is_valid():
#             raise TaskError("Form is not valid", {"form": form})
#
#         target = "sre_tasks_complete"
#
#         return target, form.cleaned_data
#
#     def context(self):
#         return {"form": self.form_class(instance=self.flow.leaving_request)}
#


class SendSRESlackMessage(Task, input="send_sre_slack_message"):
    auto = True

    def execute(self, task_info):
        user = self.flow.leaving_request.leaver_user

        send_slack_message(
            f"Please carry out leaving tasks for {user.first_name} {user.last_name}"
        )

        return None, {}


class ContactFormView(FormView):
    template_name = 'leaving/leaver_or_line_manager.html'
    form_class = LeaversForm
    success_url = '/start/'

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.send_email()
        return super().form_valid(form)
