from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional

from django.conf import settings
from django.utils import timezone
from django_workflow_engine import Task

from activity_stream.models import ActivityStreamStaffSSOUser
from core.service_now import get_service_now_interface
from core.service_now.types import AssetDetails
from core.uksbs import get_uksbs_interface
from core.uksbs.types import LeavingData, PersonData
from core.utils.lsd import inform_lsd_team_of_leaver
from core.utils.sre_messages import FailedToSendSREAlertMessage, send_sre_alert_message
from leavers.models import LeaverInformation, LeavingRequest, SlackMessage, TaskLog
from leavers.utils.emails import (
    send_csu4_leaver_email,
    send_leaver_thank_you_email,
    send_line_manager_correction_email,
    send_line_manager_notification_email,
    send_line_manager_reminder_email,
    send_line_manager_thankyou_email,
    send_ocs_leaver_email,
    send_rosa_leaver_reminder_email,
    send_rosa_line_manager_reminder_email,
    send_security_team_offboard_leaver_email,
    send_security_team_offboard_leaver_reminder_email,
    send_sre_reminder_email,
)
from leavers.utils.leaving_request import get_leaver_details


class LeavingRequestTask(Task):
    abstract = True

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.leaving_request: Optional[LeavingRequest] = getattr(
            self.flow, "leaving_request", None
        )


class BasicTask(LeavingRequestTask):
    abstract = False
    task_name = "basic_task"
    auto = True

    def execute(self, task_info):
        return None, {}, True


class CheckUKSBSLineManager(LeavingRequestTask):
    abstract = False
    task_name = "check_uksbs_line_manager"
    auto = True

    def execute(self, task_info):
        uksbs_interface = get_uksbs_interface()
        assert self.leaving_request

        # Not sure if this is the Oracle ID
        leaver_oracle_id = self.leaving_request.leaver_activitystream_user.user_id
        line_manager_oracle_id = (
            self.leaving_request.manager_activitystream_user.user_id
        )

        uksbs_leaver_hierarchy = uksbs_interface.get_user_hierarchy(
            oracle_id=leaver_oracle_id,
        )

        uksbs_leaver_managers: List[PersonData] = uksbs_leaver_hierarchy.get(
            "manager", []
        )
        uksbs_leaver_manager_oracle_ids: List[str] = [
            uksbs_leaver_manager["person_id"]
            for uksbs_leaver_manager in uksbs_leaver_managers
        ]

        if line_manager_oracle_id in uksbs_leaver_manager_oracle_ids:
            return ["notify_line_manager"], {}, True

        return ["uksbs_line_manager_correction"], {}, False


class LSDSendLeaverDetails(LeavingRequestTask):
    abstract = False
    task_name = "send_lsd_team_leaver_details"
    auto = True

    def execute(self, task_info):
        assert self.leaving_request

        leaver_name = self.leaving_request.get_leaver_name()
        if not leaver_name:
            raise Exception("No leaver name is set on the Leaving Request")
        leaver_email = self.leaving_request.get_leaver_email()
        if not leaver_email:
            raise Exception("No leaver email is set on the Leaving Request")

        inform_lsd_team_of_leaver(
            leaver_name=leaver_name,
            leaver_email=leaver_email,
        )

        return None, {}, True


class ServiceNowSendLeaverDetails(LeavingRequestTask):
    abstract = False
    task_name = "send_service_now_leaver_details"
    auto = True

    def execute(self, task_info):
        assert self.leaving_request

        leaver_details = get_leaver_details(leaving_request=self.leaving_request)

        # email: str, requester: User, assets: List[service_now_types.AssetDetails]
        leaver_information: Optional[
            LeaverInformation
        ] = self.leaving_request.leaver_information.first()

        if not leaver_information:
            raise ValueError("leaver_information is not set")

        leaver_details.update(**leaver_information.updates)

        service_now_assets: List[AssetDetails] = []

        for cirrus_asset in leaver_information.cirrus_assets:
            asset_details: AssetDetails = {
                "sys_id": cirrus_asset["sys_id"],
                "tag": cirrus_asset["tag"],
                "name": cirrus_asset["name"],
            }
            service_now_assets.append(asset_details)

        service_now_interface = get_service_now_interface()
        service_now_interface.submit_leaver_request(
            leaver_info=leaver_information,
            leaver_details=leaver_details,
            assets=service_now_assets,
        )

        return None, {}, True


class UKSBSSendLeaverDetails(LeavingRequestTask):
    abstract = False
    task_name = "send_uksbs_leaver_details"
    auto = True

    def execute(self, task_info):
        uksbs_interface = get_uksbs_interface()
        assert self.leaving_request

        leaver_as: ActivityStreamStaffSSOUser = (
            self.leaving_request.manager_activitystream_user
        )
        manager_as: ActivityStreamStaffSSOUser = (
            self.leaving_request.manager_activitystream_user
        )

        # Not sure if this is the Oracle ID
        leaver_oracle_id = leaver_as.user_id
        line_manager_oracle_id = manager_as.user_id

        uksbs_leaver_hierarchy = uksbs_interface.get_user_hierarchy(
            oracle_id=leaver_oracle_id,
        )

        uksbs_leaver: PersonData = uksbs_leaver_hierarchy["employee"][0]

        uksbs_leaver_managers: List[PersonData] = uksbs_leaver_hierarchy.get(
            "manager", []
        )
        uksbs_leaver_manager: Optional[PersonData] = None
        for ulm in uksbs_leaver_managers:
            if ulm["person_id"] == line_manager_oracle_id:
                uksbs_leaver_manager = ulm
                break

        if not uksbs_leaver_manager:
            return ["uksbs_line_manager_correction"], {}, False

        leaving_data: LeavingData = {
            # Line manager data
            "submitterName": uksbs_leaver_manager["full_name"],
            "submitterEmail": uksbs_leaver_manager["email_address"],
            "submitterOracleID": uksbs_leaver_manager["person_id"],
            "submitterDate": timezone.now().strftime("%d/%m/%Y %H:%M"),
            "submitterSelectedLineManager": uksbs_leaver_manager["full_name"],
            "submitterSelectedLineManagerEmail": uksbs_leaver_manager["email_address"],
            "submitterSelectedLineManagerOracleID": uksbs_leaver_manager["person_id"],
            "submitterSelectedLineManagerEmployeeNumber": uksbs_leaver_manager[
                "employee_number"
            ],
            # Leaver data
            "leaverName": uksbs_leaver["full_name"],
            "leaverEmail": uksbs_leaver["email_address"],
            "leaverOracleID": uksbs_leaver["person_id"],
            "leaverEmployeeNumber": uksbs_leaver["employee_number"],
            # Missing data
            "leaverPaidUnpaid": "str",
            "leaverReasonForLeaving": "str",
            "leaverLastDay": "str",
            "annualLeaveUom": "str",
            "annualLeavePaidOrDeducted": "str",
            "annualLeaveDaysPaid": "int",
            "annualLeaveHoursPaid": "int",
            "annualLeaveDaysDeducted": "int",
            "annualLeaveHoursDeducted": "int",
            "flexiPaidOrDeducted": "str",
            "flexiHoursPaid": "int",
            "flexiHoursDeducted": "int",
            "newCorrEmail": "Optional[str]",
            "newCorrAddressLine1": "Optional[str]",
            "newCorrAddressLine2": "Optional[str]",
            "newCorrAddressLine3": "Optional[str]",
            "newCorrCounty": "Optional[str]",
            "newCorrPostcode": "Optional[str]",
            "newCorrPhone": "Optional[str]",
            "directReports": "List[DirectReport]",
        }

        uksbs_interface.submit_leaver_form(data=leaving_data)

        return ["setup_scheduled_tasks"], {}, True


class EmailIds(Enum):
    LEAVER_THANK_YOU_EMAIL = "leaver_thank_you_email"
    LEAVER_ROSA_REMINDER = "leaver_rosa_reminder"
    LINE_MANAGER_ROSA_REMINDER = "line_manager_rosa_reminder"
    LINE_MANAGER_CORRECTION = "line_manager_correction"
    LINE_MANAGER_NOTIFICATION = "line_manager_notification"
    LINE_MANAGER_REMINDER = "line_manager_reminder"
    LINE_MANAGER_THANKYOU = "line_manager_thankyou"
    SECURITY_OFFBOARD_LEAVER_NOTIFICATION = "security_offboard_leaver_notification"
    SECURITY_OFFBOARD_LEAVER_REMINDER = "security_offboard_leaver_reminder"
    SRE_REMINDER = "sre_reminder"
    CSU4_EMAIL = "csu4_email"
    OCS_EMAIL = "ocs_email"


EMAIL_MAPPING: Dict[EmailIds, Callable] = {
    EmailIds.LEAVER_THANK_YOU_EMAIL: send_leaver_thank_you_email,
    EmailIds.LEAVER_ROSA_REMINDER: send_rosa_leaver_reminder_email,
    EmailIds.LINE_MANAGER_ROSA_REMINDER: send_rosa_line_manager_reminder_email,
    EmailIds.LINE_MANAGER_CORRECTION: send_line_manager_correction_email,
    EmailIds.LINE_MANAGER_NOTIFICATION: send_line_manager_notification_email,
    EmailIds.LINE_MANAGER_REMINDER: send_line_manager_reminder_email,
    EmailIds.LINE_MANAGER_THANKYOU: send_line_manager_thankyou_email,
    EmailIds.SECURITY_OFFBOARD_LEAVER_NOTIFICATION: send_security_team_offboard_leaver_email,
    EmailIds.SECURITY_OFFBOARD_LEAVER_REMINDER: send_security_team_offboard_leaver_reminder_email,
    EmailIds.SRE_REMINDER: send_sre_reminder_email,
    EmailIds.CSU4_EMAIL: send_csu4_leaver_email,
    EmailIds.OCS_EMAIL: send_ocs_leaver_email,
}


class EmailTask(LeavingRequestTask):
    abstract = True

    def should_send_email(
        self,
        task_info: Dict,
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
            raise Exception(f"Email method not found for {email_id.value}")

        if self.should_send_email(
            task_info=task_info,
            email_id=email_id,
        ):
            send_email_method(leaving_request=self.leaving_request)
            email_task_log = self.leaving_request.task_logs.create(
                task_name=f"Sending email {email_id.value}",
            )
            self.leaving_request.email_task_logs.add(email_task_log)
            self.leaving_request.save()

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
        Sends reminder emails following the following rules:
        - If the last day isn't set:
          - Send the email daily (This is going to the line manager)
        - If the last day is set
          - Send the email 2 weeks before the last day
          - Send the email 1 week before the last day
          - Send the email daily for the week before the last day
          - Send the email daily for the days after the last day
        """
        assert self.leaving_request

        last_day: Optional[datetime] = self.leaving_request.last_day
        latest_email: Optional[TaskLog] = (
            self.leaving_request.email_task_logs.filter(
                task_name__contains=email_id.value,
            )
            .order_by("-created_at")
            .first()
        )

        # If the last day isn't set, we should send the email daily.
        if not last_day:
            if not latest_email:
                return True
            else:
                next_email_date = latest_email.created_at + timedelta(days=1)
        else:
            two_weeks_before_last_day: datetime = last_day - timedelta(days=14)
            one_week_before_last_day: datetime = last_day - timedelta(days=7)

            # Work out when the next email should be sent
            if not latest_email:
                # 2 Weeks before the last day
                next_email_date = two_weeks_before_last_day
            else:
                latest_email_date = latest_email.created_at
                if latest_email_date < one_week_before_last_day:
                    # 2 week email was sent
                    next_email_date = one_week_before_last_day
                else:
                    # 1 week email was sent
                    next_email_date = latest_email_date + timedelta(days=1)

        # Send the email if the next email date has passed
        if timezone.now() >= next_email_date:
            return True
        return False


class HasLineManagerCompleted(LeavingRequestTask):
    abstract = False
    task_name = "has_line_manager_completed"
    auto = True

    def execute(self, task_info):
        # TODO: Define the conditional logic to check if the line manager has
        # completed their tasks.
        if False:
            return ["thank_line_manager"], {}, True
        return ["send_line_manager_reminder"], {}, False


class IsItLeavingDatePlusXDays(LeavingRequestTask):
    abstract = False
    task_name = "is_it_leaving_date_plus_x"
    auto = True

    def execute(self, task_info):
        print("is it x days before leaving date task executed")
        return None, {}, True


class IsItXDaysBeforePayroll(LeavingRequestTask):
    abstract = False
    task_name = "is_it_x_days_before_payroll"
    auto = True

    def execute(self, task_info):
        print("is it x days before payroll date task executed")
        return None, {}, True


class HaveSecurityCarriedOutLeavingTasks(LeavingRequestTask):
    abstract = False
    task_name = "have_security_carried_out_leaving_tasks"
    auto = True

    def execute(self, task_info):
        # TODO: Define the conditional logic to check if the Security Team have
        # completed their tasks.
        if False:
            return ["are_all_tasks_complete"], {}, True
        return ["send_security_reminder"], {}, False


class HaveSRECarriedOutLeavingTasks(LeavingRequestTask):
    abstract = False
    task_name = "have_sre_carried_out_leaving_tasks"
    auto = True

    def execute(self, task_info):
        # TODO: Define the conditional logic to check if the SRE Team have
        # completed their tasks.
        if False:
            return ["are_all_tasks_complete"], {}, True
        return ["send_sre_reminder"], {}, False


class SendSRESlackMessage(LeavingRequestTask):
    abstract = False
    auto = True
    task_name = "send_sre_slack_message"

    def execute(self, task_info):
        try:
            alert_response = send_sre_alert_message(
                leaving_request=self.leaving_request,
            )
            SlackMessage.objects.create(
                slack_timestamp=alert_response.data["ts"],
                leaving_request=self.leaving_request,
                channel_id=settings.SLACK_SRE_CHANNEL_ID,
            )
        except FailedToSendSREAlertMessage:
            print("Failed to send SRE alert message")

        return None, {}, True


class LeaverCompleteTask(LeavingRequestTask):
    abstract = False
    task_name = "leaver_complete"
    auto = True

    def execute(self, task_info):
        # TODO: Add conditional logic to check if all previous steps are complete
        if False:
            return None, {}, True
        return None, {}, False
