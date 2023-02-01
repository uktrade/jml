from datetime import timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from warnings import warn

from django.db.models.query import QuerySet
from django.utils import timezone
from django_workflow_engine import Task
from django_workflow_engine.dataclass import Step
from django_workflow_engine.models import Flow, TaskRecord

from activity_stream.models import ActivityStreamStaffSSOUser
from core.lsd_help_desk import get_lsd_help_desk_interface
from core.notify import EmailTemplates
from core.service_now import get_service_now_interface
from core.service_now.types import AssetDetails
from core.uksbs import get_uksbs_interface
from core.uksbs.client import UKSBSPersonNotFound, UKSBSUnexpectedResponse
from core.uksbs.types import PersonData
from core.utils.helpers import is_work_day_and_time
from leavers.exceptions import (
    LeaverDoesNotHaveUKSBSPersonId,
    ManagerDoesNotHaveUKSBSPersonId,
)
from leavers.models import LeaverInformation, LeavingRequest, TaskLog
from leavers.types import LeavingReason, ReminderEmailDict
from leavers.utils.emails import (
    get_leaving_request_email_personalisation,
    send_buisness_continuity_leaver_email,
    send_clu4_leaver_email,
    send_comaea_email,
    send_feetham_security_pass_office_email,
    send_health_and_safety_email,
    send_it_ops_asset_email,
    send_leaver_not_in_uksbs_reminder,
    send_leaver_thank_you_email,
    send_line_manager_correction_email,
    send_line_manager_notification_email,
    send_line_manager_offline_service_now_email,
    send_line_manager_reminder_email,
    send_line_manager_thankyou_email,
    send_ocs_leaver_email,
    send_ocs_oab_locker_email,
    send_security_team_offboard_bp_leaver_email,
    send_security_team_offboard_rk_leaver_email,
)
from leavers.utils.leaving_request import get_leaver_details


class SkipCondition(Enum):
    IS_NOT_ROSA_USER = "is_not_rosa_user"
    MANUALLY_OFFBOARDED_FROM_UKSBS = "manually_offboarded_from_uksbs"
    IS_TRANSFER = "is_transfer"
    IS_NOT_HSFL_LEAVER = "is_hsfl_leaver"


class LeavingRequestTask(Task):
    abstract = True

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        leaving_request: Optional[LeavingRequest] = getattr(
            self.flow, "leaving_request", None
        )
        if not leaving_request:
            raise Exception(
                "The Flow is missing the LeavingRequest that it relates to."
            )
        self.leaving_request: LeavingRequest = leaving_request
        self.leaving_information: Optional[
            LeaverInformation
        ] = leaving_request.leaver_information.first()

    def should_skip(self, task_info) -> bool:
        skip_conditions: List[str] = task_info.get("skip_conditions", [])
        skip_results: List[bool] = []
        for skip_condition in skip_conditions:
            if skip_condition == SkipCondition.IS_TRANSFER.value:
                skip_results.append(
                    self.leaving_request.reason_for_leaving
                    == LeavingReason.TRANSFER.value
                )

            if skip_condition == SkipCondition.MANUALLY_OFFBOARDED_FROM_UKSBS.value:
                skip_results.append(
                    bool(self.leaving_request.manually_offboarded_from_uksbs)
                )

            if skip_condition == SkipCondition.IS_NOT_ROSA_USER.value:
                skip_results.append(not self.leaving_request.is_rosa_user)

            if skip_condition == SkipCondition.IS_NOT_HSFL_LEAVER.value:
                assert self.leaving_information
                skip_results.append(
                    not self.leaving_information.is_health_and_safety_officer
                    and not self.leaving_information.is_floor_liaison_officer
                )
        return any(skip_results)


class BasicTask(LeavingRequestTask):
    abstract = False
    task_name = "basic_task"
    auto = True

    def execute(self, task_info):
        return [], True


class PauseTask(LeavingRequestTask):
    # To be used to stop the workflow from progressing until a given condition
    # is met.

    abstract = False
    task_name = "pause_task"
    auto = True

    def should_pause(self, task_info) -> bool:
        pass_condition: str = task_info.get("pass_condition", "")
        if pass_condition == "after_leaving_date" and self.leaving_request.leaving_date:
            return timezone.now() > self.leaving_request.leaving_date
        return True

    def execute(self, task_info):
        if self.should_pause(task_info):
            return [], False
        return [], True


class ConfirmLeaverData(LeavingRequestTask):
    abstract = False
    task_name = "confirm_leaver_data"
    auto = True

    def execute(self, task_info):  # noqa: C901
        uksbs_interface = get_uksbs_interface()
        assert self.leaving_request.leaver_activitystream_user
        assert self.leaving_request.manager_activitystream_user

        leaver_as_user: Optional[
            ActivityStreamStaffSSOUser
        ] = self.leaving_request.leaver_activitystream_user
        manager_as_user: Optional[
            ActivityStreamStaffSSOUser
        ] = self.leaving_request.manager_activitystream_user

        # A PII Safe list of errors with the leaving request.
        errors: List[str] = []
        uksbs_leaver_manager_person_ids: List[str] = []

        if not leaver_as_user:
            errors.append("Leaving Request doesn't have a Leaver")
        else:
            leaver_person_id = leaver_as_user.get_person_id()
            if not leaver_person_id:
                errors.append("Leaver doesn't have a UK SBS Person ID")
            else:
                try:
                    uksbs_leaver_hierarchy = uksbs_interface.get_user_hierarchy(
                        person_id=leaver_person_id,
                    )
                except UKSBSUnexpectedResponse:
                    errors.append(
                        "Couldn't get leaver hierarchy from UK SBS - Unexpected Response"
                    )
                except UKSBSPersonNotFound:
                    errors.append(
                        "Couldn't get leaver hierarchy from UK SBS - Person not found"
                    )
                else:
                    uksbs_leaver_managers: List[
                        PersonData
                    ] = uksbs_leaver_hierarchy.get("manager", [])
                    if not uksbs_leaver_managers:
                        errors.append("Leaver doesn't have a manager in UK SBS")
                    else:
                        uksbs_leaver_manager_person_ids = [
                            uksbs_leaver_manager["person_id"]
                            for uksbs_leaver_manager in uksbs_leaver_managers
                        ]
                        if len(uksbs_leaver_manager_person_ids) > 1:
                            errors.append("Leaver has more than one manager in UK SBS")
                        for uksbs_leaver_manager in uksbs_leaver_managers:
                            if not uksbs_leaver_manager["email_address"]:
                                errors.append(
                                    "Leaver's UK SBS manager doesn't have an email "
                                    "address in UK SBS"
                                )
        if not manager_as_user:
            errors.append("Leaving Request doesn't have a Manager")
        else:
            manager_person_id = manager_as_user.get_person_id()
            if not manager_person_id:
                errors.append("Manager doesn't have a UK SBS Person ID")
            else:
                try:
                    uksbs_interface.get_user_hierarchy(
                        person_id=manager_person_id,
                    )
                except UKSBSUnexpectedResponse:
                    errors.append(
                        "Couldn't get manager hierarchy from UK SBS - Unexpected "
                        "Response"
                    )
                except UKSBSPersonNotFound:
                    errors.append(
                        "Couldn't get manager hierarchy from UK SBS - Person not "
                        "found"
                    )
                else:
                    if manager_person_id not in uksbs_leaver_manager_person_ids:
                        errors.append(
                            "Manager's UK SBS Person ID is not in the leaver's "
                            "hierarchy data."
                        )

        if errors:
            error_list = "\n".join(errors)
            raise Exception(
                f"Leaving Request ({self.leaving_request.uuid}) has some issues:"
                f"\n\n{error_list}"
            )

        return [], True


class CheckUKSBSLeaver(LeavingRequestTask):
    abstract = False
    task_name = "check_uksbs_leaver"
    auto = True

    def execute(self, task_info):
        uksbs_interface = get_uksbs_interface()

        leaver_as_user: ActivityStreamStaffSSOUser = (
            self.leaving_request.leaver_activitystream_user
        )
        leaver_person_id = leaver_as_user.get_person_id()
        if not leaver_person_id:
            return ["send_leaver_not_in_uksbs_reminder"], False

        try:
            uksbs_interface.get_user_hierarchy(
                person_id=leaver_person_id,
            )
        except (UKSBSUnexpectedResponse, UKSBSPersonNotFound):
            return ["send_leaver_not_in_uksbs_reminder"], False

        return ["check_uksbs_line_manager"], True


class CheckUKSBSLineManager(LeavingRequestTask):
    abstract = False
    task_name = "check_uksbs_line_manager"
    auto = True

    def execute(self, task_info):
        uksbs_interface = get_uksbs_interface()

        leaver_as_user: ActivityStreamStaffSSOUser = (
            self.leaving_request.leaver_activitystream_user
        )
        leaver_person_id = leaver_as_user.get_person_id()
        line_manager_as_user = self.leaving_request.get_line_manager()
        manager_person_id = line_manager_as_user.get_person_id()
        if not leaver_person_id:
            raise LeaverDoesNotHaveUKSBSPersonId()
        if not manager_person_id:
            raise ManagerDoesNotHaveUKSBSPersonId()

        uksbs_leaver_hierarchy = uksbs_interface.get_user_hierarchy(
            person_id=leaver_person_id,
        )

        uksbs_leaver_managers: List[PersonData] = uksbs_leaver_hierarchy.get(
            "manager", []
        )
        uksbs_leaver_manager_person_ids: List[str] = [
            str(uksbs_leaver_manager["person_id"])
            for uksbs_leaver_manager in uksbs_leaver_managers
        ]

        if manager_person_id in uksbs_leaver_manager_person_ids:
            return ["notify_line_manager"], True

        return ["send_line_manager_correction_reminder"], False


class LSDSendLeaverDetails(LeavingRequestTask):
    abstract = False
    task_name = "send_lsd_team_leaver_details"
    auto = True

    def execute(self, task_info):
        lsd_help_desk_interface = get_lsd_help_desk_interface()
        lsd_help_desk_interface.inform_lsd_team_of_leaver(
            leaving_request=self.leaving_request,
        )
        return None, True


class ServiceNowSendLeaverDetails(LeavingRequestTask):
    abstract = False
    task_name = "send_service_now_leaver_details"
    auto = True

    def execute(self, task_info):
        leaver_details = get_leaver_details(leaving_request=self.leaving_request)
        leaver_information: Optional[
            LeaverInformation
        ] = self.leaving_request.leaver_information.first()

        if not leaver_information:
            raise ValueError("leaver_information is not set")

        leaver_details.update(**leaver_information.updates)

        service_now_assets: List[AssetDetails] = []

        if leaver_information.cirrus_assets:
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

        self.leaving_request.task_logs.create(
            task_name="Service Now informed of Leaver",
        )

        return None, True


class UKSBSSendLeaverDetails(LeavingRequestTask):
    abstract = False
    task_name = "send_uksbs_leaver_details"
    auto = True

    def execute(self, task_info):
        from core.uksbs.utils import build_leaving_data_from_leaving_request

        if self.should_skip(task_info=task_info):
            return ["are_all_tasks_complete"], True

        uksbs_interface = get_uksbs_interface()
        leaving_data = build_leaving_data_from_leaving_request(
            leaving_request=self.leaving_request,
        )

        uksbs_interface.submit_leaver_form(data=leaving_data)

        self.leaving_request.task_logs.create(
            task_name="UK SBS informed of Leaver",
        )

        return ["are_all_tasks_complete"], True


class EmailIds(Enum):
    LEAVER_THANK_YOU_EMAIL = "leaver_thank_you_email"
    LEAVER_NOT_IN_UKSBS_REMINDER = "leaver_not_in_uksbs_reminder"
    LINE_MANAGER_CORRECTION = "line_manager_correction"
    LINE_MANAGER_NOTIFICATION = "line_manager_notification"
    LINE_MANAGER_REMINDER = "line_manager_reminder"
    LINE_MANAGER_THANKYOU = "line_manager_thankyou"
    LINE_MANAGER_OFFLINE_SERVICE_NOW = "line_manager_offline_service_now"
    # Security Offboarding (Building Pass)
    SECURITY_OFFBOARD_BP_LEAVER_NOTIFICATION = (
        "security_offboard_bp_leaver_notification"
    )
    SECURITY_OFFBOARD_BP_REMINDER_DAY_AFTER_LWD = (
        "security_offboard_bp_reminder_day_after_lwd"
    )
    SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LWD = (
        "security_offboard_bp_reminder_two_days_after_lwd"
    )
    SECURITY_OFFBOARD_BP_REMINDER_ON_LD = "security_offboard_bp_reminder_on_ld"
    SECURITY_OFFBOARD_BP_REMINDER_ONE_DAY_AFTER_LD = (
        "security_offboard_bp_reminder_one_day_after_ld"
    )
    SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_LM = (
        "security_offboard_bp_reminder_two_days_after_ld_lm"
    )
    SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_PROC = (
        "security_offboard_bp_reminder_two_days_after_ld_proc"
    )
    # Security Offboarding (ROSA Kit)
    SECURITY_OFFBOARD_RK_LEAVER_NOTIFICATION = (
        "security_offboard_rk_leaver_notification"
    )
    SECURITY_OFFBOARD_RK_REMINDER_DAY_AFTER_LWD = (
        "security_offboard_rk_reminder_day_after_lwd"
    )
    SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LWD = (
        "security_offboard_rk_reminder_two_days_after_lwd"
    )
    SECURITY_OFFBOARD_RK_REMINDER_ON_LD = "security_offboard_rk_reminder_on_ld"
    SECURITY_OFFBOARD_RK_REMINDER_ONE_DAY_AFTER_LD = (
        "security_offboard_rk_reminder_one_day_after_ld"
    )
    SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LD_LM = (
        "security_offboard_rk_reminder_two_days_after_ld_lm"
    )
    SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LD_PROC = (
        "security_offboard_rk_reminder_two_days_after_ld_proc"
    )
    # SRE Offboarding
    SRE_REMINDER_DAY_AFTER_LWD = "sre_reminder_day_after_lwd"
    SRE_REMINDER_ONE_DAY_AFTER_LD = "sre_reminder_one_day_after_ld"
    SRE_REMINDER_TWO_DAYS_AFTER_LD_PROC = "sre_reminder_two_days_after_ld_proc"

    FEETHAM_SECURITY_PASS_OFFICE_EMAIL = "feetham_security_pass_office_email"
    IT_OPS_ASSET_EMAIL = "it_ops_asset_email"
    CLU4_EMAIL = "clu4_email"
    OCS_EMAIL = "ocs_email"
    OCS_OAB_LOCKER_EMAIL = "ocs_oab_locker_email"
    HEALTH_AND_SAFETY_EMAIL = "health_and_safety_email"
    COMAEA_EMAIL = "comaea_email"
    BUISNESS_CONTINUITY_LEAVER_EMAIL = "buisness_continuity_leaver_email"


EMAIL_MAPPING: Dict[EmailIds, Callable] = {
    EmailIds.LEAVER_THANK_YOU_EMAIL: send_leaver_thank_you_email,
    EmailIds.LEAVER_NOT_IN_UKSBS_REMINDER: send_leaver_not_in_uksbs_reminder,
    EmailIds.LINE_MANAGER_CORRECTION: send_line_manager_correction_email,
    EmailIds.LINE_MANAGER_NOTIFICATION: send_line_manager_notification_email,
    EmailIds.LINE_MANAGER_REMINDER: send_line_manager_reminder_email,
    EmailIds.LINE_MANAGER_THANKYOU: send_line_manager_thankyou_email,
    EmailIds.LINE_MANAGER_OFFLINE_SERVICE_NOW: send_line_manager_offline_service_now_email,
    EmailIds.SECURITY_OFFBOARD_BP_LEAVER_NOTIFICATION: send_security_team_offboard_bp_leaver_email,
    EmailIds.SECURITY_OFFBOARD_RK_LEAVER_NOTIFICATION: send_security_team_offboard_rk_leaver_email,
    EmailIds.FEETHAM_SECURITY_PASS_OFFICE_EMAIL: send_feetham_security_pass_office_email,
    EmailIds.IT_OPS_ASSET_EMAIL: send_it_ops_asset_email,
    EmailIds.CLU4_EMAIL: send_clu4_leaver_email,
    EmailIds.OCS_EMAIL: send_ocs_leaver_email,
    EmailIds.OCS_OAB_LOCKER_EMAIL: send_ocs_oab_locker_email,
    EmailIds.HEALTH_AND_SAFETY_EMAIL: send_health_and_safety_email,
    EmailIds.COMAEA_EMAIL: send_comaea_email,
    EmailIds.BUISNESS_CONTINUITY_LEAVER_EMAIL: send_buisness_continuity_leaver_email,
}
PROCESSOR_REMINDER_EMAIL_MAPPING: Dict[EmailIds, EmailTemplates] = {
    # Security Offboarding (Building Pass)
    EmailIds.SECURITY_OFFBOARD_BP_REMINDER_DAY_AFTER_LWD: (
        EmailTemplates.SECURITY_OFFBOARD_BP_REMINDER_DAY_AFTER_LWD
    ),
    EmailIds.SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LWD: (
        EmailTemplates.SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LWD
    ),
    EmailIds.SECURITY_OFFBOARD_BP_REMINDER_ON_LD: (
        EmailTemplates.SECURITY_OFFBOARD_BP_REMINDER_ON_LD
    ),
    EmailIds.SECURITY_OFFBOARD_BP_REMINDER_ONE_DAY_AFTER_LD: (
        EmailTemplates.SECURITY_OFFBOARD_BP_REMINDER_ONE_DAY_AFTER_LD
    ),
    EmailIds.SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_LM: (
        EmailTemplates.SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_LM
    ),
    EmailIds.SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_PROC: (
        EmailTemplates.SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_PROC
    ),
    # Security Offboarding (Rosa Kit)
    EmailIds.SECURITY_OFFBOARD_RK_REMINDER_DAY_AFTER_LWD: (
        EmailTemplates.SECURITY_OFFBOARD_RK_REMINDER_DAY_AFTER_LWD
    ),
    EmailIds.SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LWD: (
        EmailTemplates.SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LWD
    ),
    EmailIds.SECURITY_OFFBOARD_RK_REMINDER_ON_LD: (
        EmailTemplates.SECURITY_OFFBOARD_RK_REMINDER_ON_LD
    ),
    EmailIds.SECURITY_OFFBOARD_RK_REMINDER_ONE_DAY_AFTER_LD: (
        EmailTemplates.SECURITY_OFFBOARD_RK_REMINDER_ONE_DAY_AFTER_LD
    ),
    EmailIds.SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LD_LM: (
        EmailTemplates.SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LD_LM
    ),
    EmailIds.SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LD_PROC: (
        EmailTemplates.SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LD_PROC
    ),
    # SRE Offboarding
    EmailIds.SRE_REMINDER_DAY_AFTER_LWD: (EmailTemplates.SRE_REMINDER_DAY_AFTER_LWD),
    EmailIds.SRE_REMINDER_ONE_DAY_AFTER_LD: (
        EmailTemplates.SRE_REMINDER_ONE_DAY_AFTER_LD
    ),
    EmailIds.SRE_REMINDER_TWO_DAYS_AFTER_LD_PROC: (
        EmailTemplates.SRE_REMINDER_TWO_DAYS_AFTER_LD_PROC
    ),
}

SECURITY_TEAM_BP_REMINDER_EMAILS: ReminderEmailDict = {
    "day_after_lwd": EmailIds.SECURITY_OFFBOARD_BP_REMINDER_DAY_AFTER_LWD.value,
    "two_days_after_lwd": EmailIds.SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LWD.value,
    "on_ld": EmailIds.SECURITY_OFFBOARD_BP_REMINDER_ON_LD.value,
    "one_day_after_ld": EmailIds.SECURITY_OFFBOARD_BP_REMINDER_ONE_DAY_AFTER_LD.value,
    "two_days_after_ld_lm": EmailIds.SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_LM.value,
    "two_days_after_ld_proc": (
        EmailIds.SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_PROC.value
    ),
}

SECURITY_TEAM_RK_REMINDER_EMAILS: ReminderEmailDict = {
    "day_after_lwd": EmailIds.SECURITY_OFFBOARD_RK_REMINDER_DAY_AFTER_LWD.value,
    "two_days_after_lwd": EmailIds.SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LWD.value,
    "on_ld": EmailIds.SECURITY_OFFBOARD_RK_REMINDER_ON_LD.value,
    "one_day_after_ld": EmailIds.SECURITY_OFFBOARD_RK_REMINDER_ONE_DAY_AFTER_LD.value,
    "two_days_after_ld_lm": EmailIds.SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LD_LM.value,
    "two_days_after_ld_proc": (
        EmailIds.SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LD_PROC.value
    ),
}

SRE_REMINDER_EMAILS: ReminderEmailDict = {
    "day_after_lwd": EmailIds.SRE_REMINDER_DAY_AFTER_LWD.value,
    "two_days_after_lwd": None,
    "on_ld": None,
    "one_day_after_ld": EmailIds.SRE_REMINDER_ONE_DAY_AFTER_LD.value,
    "two_days_after_ld_lm": None,
    "two_days_after_ld_proc": EmailIds.SRE_REMINDER_TWO_DAYS_AFTER_LD_PROC.value,
}
SRE_REMINDER_EMAIL_IDS: List[EmailIds] = [
    EmailIds(sre_reminder_email_id)  # type: ignore
    for _, sre_reminder_email_id in SRE_REMINDER_EMAILS.items()
    if sre_reminder_email_id
]


class EmailTask(LeavingRequestTask):
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

    def get_send_email_method(self, email_id: EmailIds) -> Callable:
        send_email_method: Optional[Callable] = EMAIL_MAPPING.get(email_id, None)

        if not send_email_method:
            raise Exception(f"Email method not found for {email_id.value}")

        return send_email_method

    def send_email(
        self, email_id: EmailIds, template_id: Optional[EmailTemplates] = None
    ):
        """
        Send the email.
        """

        if self.should_send_email(
            email_id=email_id,
        ):
            send_email_method = self.get_send_email_method(email_id=email_id)
            send_email_method(
                leaving_request=self.leaving_request,
                template_id=template_id,
            )
            email_task_log = self.leaving_request.task_logs.create(
                task_name=f"Sending email {email_id.value}",
            )
            self.leaving_request.email_task_logs.add(email_task_log)
            self.leaving_request.save()

    def execute(self, task_info):
        if not is_work_day_and_time(timezone.now()):
            return None, False

        if not self.should_skip(task_info=task_info):
            email_id: EmailIds = EmailIds(task_info["email_id"])
            self.send_email(email_id=email_id)
        return None, True


class NotificationEmail(EmailTask):
    abstract = False
    task_name = "notification_email"
    auto = True


class DailyReminderEmail(EmailTask):
    abstract = False
    task_name = "daily_reminder_email"
    auto = True

    def should_send_email(
        self,
        email_id: EmailIds,
    ) -> bool:
        latest_email: Optional[TaskLog] = (
            self.leaving_request.email_task_logs.filter(
                task_name__contains=email_id.value,
            )
            .order_by("-created_at")
            .first()
        )

        if not latest_email:
            return True

        next_email_date = latest_email.created_at + timedelta(days=1)
        # Send the email if the next email date has passed
        if timezone.now() >= next_email_date:
            return True
        return False


class ReminderEmail(EmailTask):
    abstract = False
    task_name = "reminder_email"
    auto = True

    def should_send_email(
        self,
        email_id: EmailIds,
    ) -> bool:
        """
        Sends reminder emails following the following rules:
        - If the last day isn't set:
          - Send the email daily (This is going to the Line Manager)
        - If the last day is set
          - Send the email 2 weeks before the last day
          - Send the email 1 week before the last day
          - Send the email daily for the week before the last day
          - Send the email daily for the days after the last day
        """
        last_day = self.leaving_request.get_last_day()
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
            two_weeks_before_last_day = last_day - timedelta(days=14)
            one_week_before_last_day = last_day - timedelta(days=7)

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


class ProcessorReminderEmail(EmailTask):
    abstract = False
    task_name = "processor_reminder_email"
    auto = True

    day_after_lwd_email_id: Optional[EmailIds] = None
    two_days_after_lwd_email_id: Optional[EmailIds] = None
    on_ld_email_id: Optional[EmailIds] = None
    one_day_after_ld_email_id: Optional[EmailIds] = None
    two_days_after_ld_lm_email_id: Optional[EmailIds] = None
    two_days_after_ld_proc_email_id: Optional[EmailIds] = None

    def should_send_email(
        self,
        email_id: EmailIds,
    ) -> bool:
        already_sent = self.leaving_request.email_task_logs.filter(
            task_name__contains=email_id.value,
        ).exists()

        return not already_sent

    def get_send_email_method(self, email_id: EmailIds) -> Callable:
        def send_processor_message(
            leaving_request: LeavingRequest, template_id: Optional[EmailTemplates]
        ):
            if email_id in SRE_REMINDER_EMAIL_IDS:
                # We only send slack messages to SRE (but we prentend to send
                # an email)
                from core.utils.sre_messages import send_sre_reminder_message

                send_sre_reminder_message(
                    email_id=email_id, leaving_request=leaving_request
                )
            else:
                # For everyone else we always send emails
                from core import notify

                assert template_id
                notify.email(
                    email_addresses=self.processor_emails,
                    template_id=template_id,
                    personalisation=get_leaving_request_email_personalisation(
                        leaving_request
                    ),
                )

        def send_line_manager_email(
            leaving_request: LeavingRequest, template_id: Optional[EmailTemplates]
        ):
            assert template_id
            from core import notify

            manager_as_user = leaving_request.get_line_manager()
            assert manager_as_user

            manager_contact_emails = manager_as_user.get_email_addresses_for_contact()

            notify.email(
                email_addresses=manager_contact_emails,
                template_id=template_id,
                personalisation=get_leaving_request_email_personalisation(
                    leaving_request
                ),
            )

        processor_email_mapping = [
            item
            for item in [
                self.day_after_lwd_email_id,
                self.one_day_after_ld_email_id,
                self.two_days_after_ld_proc_email_id,
            ]
            if item is not None
        ]
        line_manager_email_mapping = [
            item
            for item in [
                self.two_days_after_lwd_email_id,
                self.on_ld_email_id,
                self.two_days_after_ld_lm_email_id,
            ]
            if item is not None
        ]

        if email_id in processor_email_mapping:
            return send_processor_message
        elif email_id in line_manager_email_mapping:
            return send_line_manager_email

        raise Exception(f"Email method not found for {email_id.value}")

    def send_day_after_last_working_day_email(self, task_info: Dict[Any, Any]):
        today = timezone.now()
        last_working_day = self.leaving_request.get_last_day()
        if not last_working_day:
            raise Exception("Leaving Request doesn't have a last working day")

        day_after_last_working_day = last_working_day + timedelta(days=1)

        day_after_lwd: Optional[str] = task_info.get("day_after_lwd")
        if day_after_lwd and today >= day_after_last_working_day:
            self.day_after_lwd_email_id = EmailIds(day_after_lwd)
            template_id = PROCESSOR_REMINDER_EMAIL_MAPPING[self.day_after_lwd_email_id]
            self.send_email(
                email_id=self.day_after_lwd_email_id,
                template_id=template_id,
            )

    def send_two_days_after_last_working_day_email(self, task_info: Dict[Any, Any]):
        today = timezone.now()
        last_working_day = self.leaving_request.get_last_day()
        if not last_working_day:
            raise Exception("Leaving Request doesn't have a last working day")

        two_days_after_last_working_day = last_working_day + timedelta(days=2)
        two_days_after_lwd: Optional[str] = task_info.get("two_days_after_lwd")
        if two_days_after_lwd and today >= two_days_after_last_working_day:
            self.two_days_after_lwd_email_id = EmailIds(two_days_after_lwd)
            template_id = PROCESSOR_REMINDER_EMAIL_MAPPING[
                self.two_days_after_lwd_email_id
            ]
            self.send_email(
                email_id=self.two_days_after_lwd_email_id,
                template_id=template_id,
            )

    def send_on_leaving_date_email(self, task_info: Dict[Any, Any]):
        today = timezone.now()
        leaving_date = self.leaving_request.get_leaving_date()
        if not leaving_date:
            raise Exception("Leaving Request doesn't have a leaving date")

        on_ld: Optional[str] = task_info.get("on_ld")
        if on_ld and today >= leaving_date:
            self.on_ld_email_id = EmailIds(on_ld)
            template_id = PROCESSOR_REMINDER_EMAIL_MAPPING[self.on_ld_email_id]
            self.send_email(email_id=self.on_ld_email_id, template_id=template_id)

    def send_one_day_after_leaving_date_email(self, task_info: Dict[Any, Any]):
        today = timezone.now()
        leaving_date = self.leaving_request.get_leaving_date()
        if not leaving_date:
            raise Exception("Leaving Request doesn't have a leaving date")

        day_after_leaving_date = leaving_date + timedelta(days=1)
        one_day_after_ld: Optional[str] = task_info.get("one_day_after_ld")
        if one_day_after_ld and today >= day_after_leaving_date:
            self.one_day_after_ld_email_id = EmailIds(one_day_after_ld)
            template_id = PROCESSOR_REMINDER_EMAIL_MAPPING[
                self.one_day_after_ld_email_id
            ]
            self.send_email(
                email_id=self.one_day_after_ld_email_id,
                template_id=template_id,
            )

    def send_two_days_after_leaving_date_line_manager_email(
        self, task_info: Dict[Any, Any]
    ):
        today = timezone.now()
        leaving_date = self.leaving_request.get_leaving_date()
        if not leaving_date:
            raise Exception("Leaving Request doesn't have a leaving date")

        two_days_after_leaving_date = leaving_date + timedelta(days=2)
        if today >= two_days_after_leaving_date:
            two_days_after_ld_lm: Optional[str] = task_info.get("two_days_after_ld_lm")
            if two_days_after_ld_lm:
                self.two_days_after_ld_lm_email_id = EmailIds(two_days_after_ld_lm)
                template_id = PROCESSOR_REMINDER_EMAIL_MAPPING[
                    self.two_days_after_ld_lm_email_id
                ]
                self.send_email(
                    email_id=self.two_days_after_ld_lm_email_id,
                    template_id=template_id,
                )

    def send_two_days_after_leaving_date_processor_email(
        self, task_info: Dict[Any, Any]
    ):
        today = timezone.now()
        leaving_date = self.leaving_request.get_leaving_date()
        if not leaving_date:
            raise Exception("Leaving Request doesn't have a leaving date")

        two_days_after_leaving_date = leaving_date + timedelta(days=2)
        if today >= two_days_after_leaving_date:
            two_days_after_ld_proc: Optional[str] = task_info.get(
                "two_days_after_ld_proc"
            )
            if two_days_after_ld_proc:
                self.two_days_after_ld_proc_email_id = EmailIds(two_days_after_ld_proc)
                template_id = PROCESSOR_REMINDER_EMAIL_MAPPING[
                    self.two_days_after_ld_proc_email_id
                ]
                self.send_email(
                    email_id=self.two_days_after_ld_proc_email_id,
                    template_id=template_id,
                )

    def execute(self, task_info):
        """
        Key:
         - lwd = Last Working Day
         - ld = Leaving Date
         - lm = Line Manager
         - proc = Processor
        """

        if self.should_skip(task_info=task_info):
            return None, True

        # Check to see if it is a work day
        if not is_work_day_and_time(timezone.now()):
            return None, False

        self.processor_emails: List[str] = task_info["processor_emails"]

        last_working_day = self.leaving_request.get_last_day()
        leaving_date = self.leaving_request.get_leaving_date()

        assert last_working_day
        assert leaving_date

        # Only send "X days after Last working day" emails if the Last working
        # day is not the same as the leaving date.
        if last_working_day.date() != leaving_date.date():
            # Day after Last working day
            self.send_day_after_last_working_day_email(task_info=task_info)

            # 2 days after Last working day
            self.send_two_days_after_last_working_day_email(task_info=task_info)

        # Leaving date
        self.send_on_leaving_date_email(task_info=task_info)

        # Day after Leaving date
        self.send_one_day_after_leaving_date_email(task_info=task_info)

        # Two days after Leaving date
        self.send_two_days_after_leaving_date_line_manager_email(
            task_info=task_info,
        )

        self.send_two_days_after_leaving_date_processor_email(
            task_info=task_info,
        )

        return None, True


class HasLineManagerCompleted(LeavingRequestTask):
    abstract = False
    task_name = "has_line_manager_completed"
    auto = True

    def execute(self, task_info):
        if self.leaving_request.line_manager_complete:
            return ["thank_line_manager"], True
        return ["send_line_manager_reminder"], False


class IsItXDaysBeforePayroll(LeavingRequestTask):
    abstract = False
    task_name = "is_it_x_days_before_payroll"
    auto = True

    def execute(self, task_info):
        print("is it x days before payroll date task executed")
        return None, True


class HaveSecurityCarriedOutBuildingPassLeavingTasks(LeavingRequestTask):
    abstract = False
    task_name = "have_security_carried_out_bp_leaving_tasks"
    auto = True

    def execute(self, task_info):
        if (
            self.leaving_request.security_team_complete
            or self.leaving_request.security_team_building_pass_complete
        ):
            return ["are_all_tasks_complete"], True
        return ["send_security_bp_reminder"], False


class HaveSecurityCarriedOutRosaKitLeavingTasks(LeavingRequestTask):
    abstract = False
    task_name = "have_security_carried_out_rk_leaving_tasks"
    auto = True

    def execute(self, task_info):
        if not self.leaving_request.is_rosa_user:
            return ["are_all_tasks_complete"], True

        if (
            self.leaving_request.security_team_complete
            or self.leaving_request.security_team_rosa_kit_complete
        ):
            return ["are_all_tasks_complete"], True

        return ["send_security_rk_reminder"], False


class HaveSRECarriedOutLeavingTasks(LeavingRequestTask):
    abstract = False
    task_name = "have_sre_carried_out_leaving_tasks"
    auto = True

    def execute(self, task_info):
        if self.leaving_request.sre_complete:
            return ["are_all_tasks_complete"], True
        return ["send_sre_reminder"], False


# TODO: Remove this task in the future
class SendSRESlackMessage(LeavingRequestTask):
    abstract = False
    auto = True
    task_name = "send_sre_slack_message"

    def __init__(self, *args, **kwargs):
        warn(
            f"{self.__class__.__name__} is deprecated and will be removed in the future.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

    def execute(self, task_info):
        from core.utils.sre_messages import (
            FailedToSendSREAlertMessage,
            send_sre_alert_message,
        )

        try:
            send_sre_alert_message(
                leaving_request=self.leaving_request,
            )
        except FailedToSendSREAlertMessage:
            print("Failed to send SRE alert message")

        return None, True


class HasLineManagerUpdaatedServiceNow(LeavingRequestTask):
    abstract = False
    task_name = "has_line_manager_updated_service_now"
    auto = True

    def execute(self, task_info):
        if (
            not self.leaving_request.service_now_offline
            or self.leaving_request.line_manager_service_now_complete
        ):
            return ["are_all_tasks_complete"], True

        return ["send_line_manager_offline_service_now_reminder"], False


class LeaverCompleteTask(LeavingRequestTask):
    abstract = False
    task_name = "leaver_complete"
    auto = True

    def execute(self, task_info):
        task_record: TaskRecord = self.task_record
        flow: Flow = self.flow

        leaver_complete_step: Step = flow.workflow.get_step(task_record.step_id)

        # Get all steps that point to the current step.
        previous_steps: List[Step] = [
            step
            for step in flow.workflow.steps
            if step.targets != "complete"
            and leaver_complete_step.step_id in step.targets
        ]

        all_previous_steps_complete: bool = True

        for previous_step in previous_steps:
            previous_step_tasks: QuerySet[TaskRecord] = flow.tasks.filter(
                step_id=previous_step.step_id
            )
            if not previous_step_tasks.filter(done=True).exists():
                all_previous_steps_complete = False
                break

        if all_previous_steps_complete:
            return None, True
        return None, False
