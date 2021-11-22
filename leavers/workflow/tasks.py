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


class BasicTask(Task):
    task_name = "basic_task"
    auto = True

    def execute(self, task_info):
        return None, {}


class NotificationEmail(Task):
    task_name = "notification_email"
    auto = True

    def execute(self, task_info):
        print("Notification email task executed...")
        return None, {}


class IsItXDaysBeforeLeavingDate(Task):
    task_name = "is_it_leaving_date_plus_x"
    auto = True

    def execute(self, task_info):
        print("is it x days before leaving date task executed")
        return None, {}


class SendSRESlackMessage(Task):
    auto = True
    task_name = "send_sre_slack_message"

    def execute(self, task_info):
        user = self.flow.leaving_request.leaver_user

        send_slack_message(
            f"Please carry out leaving tasks for {user.first_name} {user.last_name}"
        )

        return None, {}


class SREEConfirmTasksComplete(Task):
    auto = False
    form_class = SREConfirmCompleteForm
    template = "flow/basic_form.html"
    task_name = "sre_confirm_tasks_complete"

    def execute(self, task_info):
        form = self.form_class(data=task_info)

        if not form.is_valid():
            raise TaskError("Form is not valid", {"form": form})

        target = "sre_tasks_complete"

        return target, form.cleaned_data

    def context(self):
        return {"form": self.form_class()}



