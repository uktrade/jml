from django_workflow_engine import (
    Task,
)
from django.conf import settings

from core.utils.sre_messages import (
    FailedToSendSREAlertMessage,
    send_sre_alert_message,
)

from leavers.models import SlackMessage


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
        leaver = self.flow.leaving_request.leaver_user

        try:
            alert_response = send_sre_alert_message(
                first_name=leaver.first_name,
                last_name=leaver.last_name,
                leaving_request=self.flow.leaving_request,
            )
            SlackMessage.objects.create(
                slack_timestamp=alert_response.data["ts"],
                leaving_request=self.flow.leaving_request,
                channel_id=settings.SLACK_SRE_CHANNEL_ID,
            )
        except FailedToSendSREAlertMessage:
            print("Failed to send SRE alert message")

        return None, {}


# class SREEConfirmTasksComplete(Task):
#     auto = False
#     form_class = SREConfirmCompleteForm
#     template = "flow/basic_form.html"
#     task_name = "sre_confirm_tasks_complete"
#
#     def execute(self, task_info):
#         form = self.form_class(data=task_info)
#
#         if not form.is_valid():
#             raise TaskError("Form is not valid", {"form": form})
#
#         target = "sre_tasks_complete"
#
#         return target, form.cleaned_data
#
#     def context(self):
#         return {"form": self.form_class()}



