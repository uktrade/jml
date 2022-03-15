from enum import Enum
from typing import Callable, Dict, Optional

from django.conf import settings
from django.core.cache import cache
from django_workflow_engine import Task

from core.utils.sre_messages import FailedToSendSREAlertMessage, send_sre_alert_message
from leavers.models import SlackMessage
from leavers.utils import (
    send_csu4_leaver_email,
    send_line_manager_notification_email,
    send_ocs_leaver_email,
    send_rosa_leaver_reminder_email,
    send_rosa_line_manager_reminder_email,
    send_security_team_offboard_leaver_email,
    send_security_team_offboard_leaver_reminder_email,
    send_sre_reminder_email,
)


class BasicTask(Task):
    task_name = "basic_task"
    auto = True

    def execute(self, task_info):
        return None, {}, True


class EmailIds(Enum):
    LEAVER_ROSA_REMINDER = "leaver_rosa_reminder"
    LINE_MANAGER_ROSA_REMINDER = "line_manager_rosa_reminder"
    LINE_MANAGER_NOTIFICATION = "line_manager_notification"
    LINE_MANAGER_REMINDER = "line_manager_reminder"
    LINE_MANAGER_THANKYOU = "line_manager_thankyou"
    SECURITY_OFFBOARD_LEAVER_NOTIFICATION = "security_offboard_leaver_notification"
    SECURITY_OFFBOARD_LEAVER_REMINDER = "security_offboard_leaver_reminder"
    SRE_REMINDER = "sre_reminder"
    CSU4_EMAIL = "csu4_email"
    OCS_EMAIL = "ocs_email"


EMAIL_MAPPING: Dict[EmailIds, Callable] = {
    EmailIds.LEAVER_ROSA_REMINDER: send_rosa_leaver_reminder_email,
    EmailIds.LINE_MANAGER_ROSA_REMINDER: send_rosa_line_manager_reminder_email,
    EmailIds.LINE_MANAGER_NOTIFICATION: send_line_manager_notification_email,
    EmailIds.LINE_MANAGER_REMINDER: None,
    EmailIds.LINE_MANAGER_THANKYOU: None,
    EmailIds.SECURITY_OFFBOARD_LEAVER_NOTIFICATION: send_security_team_offboard_leaver_email,
    EmailIds.SECURITY_OFFBOARD_LEAVER_REMINDER: send_security_team_offboard_leaver_reminder_email,
    EmailIds.SRE_REMINDER: send_sre_reminder_email,
    EmailIds.CSU4_EMAIL: send_csu4_leaver_email,
    EmailIds.OCS_EMAIL: send_ocs_leaver_email,
}


class EmailTask(Task):
    abstract = True

    def should_send_email(
        self,
        email_id: EmailIds,
    ) -> bool:
        """
        Check if we should send the email.
        This method can be used to prevent the task from sending the email.

        Example scenarios:
        - Email no longer needed
        - Email was sent recently and we only want to send evert X mins/days/hours
        """
        return True

    def execute(self, task_info):
        email_id: EmailIds = EmailIds(task_info["email_id"])
        send_email_method: Optional[Callable] = EMAIL_MAPPING.get(email_id, None)

        if not send_email_method:
            raise Exception(f"Email method not found for {email_id}")

        if self.should_send_email():
            send_email_method(leaving_request=self.flow.leaving_request)

        return None, {}, True


class NotificationEmail(EmailTask):
    abstract = False
    task_name = "notification_email"
    auto = True


class ReminderEmail(EmailTask):
    abstract = False
    task_name = "reminder_email"
    auto = True

    def should_send_email(
        self,
        task_info: Dict,
        email_id: EmailIds,
    ) -> bool:
        """
        Check if the email has been sent recently, if not then return True and cache that
        we have sent the email.
        """
        cache_key = email_id + "_" + self.flow.leaving_request.id
        sent_email = cache.get(cache_key)
        if not sent_email:
            cache.set(cache_key, True, task_info.get("reminder_wait_time", 86400))
            return True


class HasLineManagerCompleted(Task):
    task_name = "has_line_manager_completed"
    auto = True

    def execute(self, task_info):
        # TODO: Define the conditional logic to check if the line manager has
        # completed their tasks.
        if False:
            return ["thank_line_manager"], {}, True
        return ["send_line_manager_reminder"], {}, False


class IsItLeavingDatePlusXDays(Task):
    task_name = "is_it_leaving_date_plus_x"
    auto = True

    def execute(self, task_info):
        print("is it x days before leaving date task executed")
        return None, {}, True


class IsItXDaysBeforePayroll(Task):
    task_name = "is_it_x_days_before_payroll"
    auto = True

    def execute(self, task_info):
        print("is it x days before payroll date task executed")
        return None, {}, True


class HaveSecurityCarriedOutLeavingTasks(Task):
    task_name = "have_security_carried_out_leaving_tasks"
    auto = True

    def execute(self, task_info):
        # TODO: Define the conditional logic to check if the Security Team have
        # completed their tasks.
        if False:
            return ["are_all_tasks_complete"], {}, True
        return ["send_security_reminder"], {}, False


class HaveSRECarriedOutLeavingTasks(Task):
    task_name = "have_sre_carried_out_leaving_tasks"
    auto = True

    def execute(self, task_info):
        # TODO: Define the conditional logic to check if the SRE Team have
        # completed their tasks.
        if False:
            return ["are_all_tasks_complete"], {}, True
        return ["send_sre_reminder"], {}, False


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

        return None, {}, True


class LeaverCompleteTask(Task):
    task_name = "leaver_complete"
    auto = True

    def execute(self, task_info):
        # TODO: Add conditional logic to check if all previous steps are complete
        if False:
            return None, {}, True
        return None, {}, False
