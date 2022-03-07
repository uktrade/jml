from enum import Enum
from typing import Callable, Dict, Optional

from django.conf import settings
from django_workflow_engine import Task

from core.utils.sre_messages import FailedToSendSREAlertMessage, send_sre_alert_message
from leavers.models import SlackMessage
from leavers.utils import send_csu4_leaver_email, send_ocs_leaver_email


class BasicTask(Task):
    task_name = "basic_task"
    auto = True

    def execute(self, task_info):
        return None, {}


class EmailIds(Enum):
    LINE_MANAGER_NOTIFICATION = "line_manager_notification"
    LINE_MANAGER_REMINDER = "line_manager_reminder"
    LINE_MANAGER_THANKYOU = "line_manager_thankyou"
    SRE_REMINDER = "sre_reminder"
    HR_LEAVER_NOTIFICATION = "hr_leaver_notification"
    HR_TASKS_NOTIFICATION = "hr_tasks_notification"
    HR_REMINDER = "hr_reminder"
    CSU4_EMAIL = "csu4_email"
    OCS_EMAIL = "ocs_email"


EMAIL_MAPPING: Dict[EmailIds, Callable] = {
    EmailIds.LINE_MANAGER_NOTIFICATION: None,
    EmailIds.LINE_MANAGER_REMINDER: None,
    EmailIds.LINE_MANAGER_THANKYOU: None,
    EmailIds.SRE_REMINDER: None,
    EmailIds.HR_LEAVER_NOTIFICATION: None,
    EmailIds.HR_TASKS_NOTIFICATION: None,
    EmailIds.HR_REMINDER: None,
    EmailIds.CSU4_EMAIL: send_csu4_leaver_email,
    EmailIds.OCS_EMAIL: send_ocs_leaver_email,
}


class NotificationEmail(Task):
    task_name = "notification_email"
    auto = True

    def execute(self, task_info):
        email_id: EmailIds = task_info["email_id"]
        send_email_method: Optional[Callable] = EMAIL_MAPPING.get(email_id, None)

        if not send_csu4_leaver_email:
            raise Exception(f"Email method not found for {email_id}")

        send_email_method(leaving_request=self.flow.leaving_request)

        return None, {}


class HasLineManagerCompleted(Task):
    task_name = "has_line_manager_completed"
    auto = True

    def execute(self, task_info):
        return ["send_line_manager_reminder"], {}


class IsItLeavingDatePlusXDays(Task):
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
    task_name = "have_sre_carried_out_leaving_tasks"
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


class HaveHRCarriedOutLeavingTasks(Task):
    task_name = "have_hr_carried_out_leaving_tasks"
    auto = True

    def execute(self, task_info):
        return None, {}


class LeaverCompleteTask(Task):
    task_name = "leaver_complete"
    auto = True

    def execute(self, task_info):
        return None, {}
