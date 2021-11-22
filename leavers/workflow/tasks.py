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


class IsItLeavingDatePlusXdays(Task):
    task_name = "is_it_leaving_date_plus_x"
    auto = True

    def execute(self, task_info):
        print("is it x days before leaving date task executed")
        return None, {}


class IsItXDaysBeforePayroll(Task):
    task_name = "is_it_x_days_before_payroll"
    auto = True

    def execute(self, task_info):
        print("is it x days before payroll date task executed")
        return None, {}


class HaveSRECarriedOutLeavingTasks(Task):
    task_name = "have_SRE_carried_out_leaving_tasks"
    auto = True

    def execute(self, task_info):
        return None, {}


class SendSRESlackMessage(Task):
    auto = True
    task_name = "send_sre_slack_message"

    def execute(self, task_info):
        try:
            alert_response = send_sre_alert_message(
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
