import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Tuple, cast

from django.contrib.auth import get_user_model
from django.db import models

from activity_stream.models import (
    ActivityStreamStaffSSOUser,
    ActivityStreamStaffSSOUserEmail,
)
from core.types import Address
from leavers.forms.line_manager import (
    AnnualLeavePaidOrDeducted,
    DaysHours,
    FlexiLeavePaidOrDeducted,
    LeaverPaidUnpaid,
    ReasonForleaving,
)
from leavers.types import (
    LeavingRequestReminderEmailTasks,
    ReturnOptions,
    SecurityClearance,
    StaffType,
)

if TYPE_CHECKING:
    from leavers.workflow.tasks import EmailIds


class TaskLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    task_name = models.CharField(max_length=155)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="task_logs",
        blank=True,
        null=True,
    )
    notes = models.CharField(max_length=1000, blank=True, null=True)


class LeavingRequest(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4)
    flow = models.OneToOneField(
        "django_workflow_engine.Flow",
        models.CASCADE,
        related_name="leaving_request",
        null=True,
        blank=True,
    )

    requested_at = models.DateTimeField(auto_now_add=True)
    requested_by = models.CharField(
        max_length=255,
    )  # SSO id

    last_day = models.DateTimeField(null=True, blank=True)
    leaving_date = models.DateTimeField(null=True, blank=True)

    user_requesting = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="requesting_users",
    )
    leaver_activitystream_user = models.ForeignKey(
        ActivityStreamStaffSSOUser,
        on_delete=models.CASCADE,
        related_name="+",
    )
    # The manager that the Leaver selected
    manager_activitystream_user = models.ForeignKey(
        ActivityStreamStaffSSOUser,
        on_delete=models.CASCADE,
        related_name="+",
        blank=True,
        null=True,
    )
    data_recipient_activitystream_user = models.ForeignKey(
        ActivityStreamStaffSSOUser,
        on_delete=models.CASCADE,
        related_name="+",
        blank=True,
        null=True,
    )
    is_rosa_user = models.BooleanField(null=True, blank=True)
    holds_government_procurement_card = models.BooleanField(null=True, blank=True)
    security_clearance = models.CharField(
        choices=SecurityClearance.choices,
        max_length=255,
        blank=True,
        null=True,
    )
    staff_type = models.CharField(
        choices=StaffType.choices,
        max_length=255,
        blank=True,
        null=True,
    )

    leaver_complete = models.DateTimeField(null=True, blank=True)

    """
    Task Logs
    """

    task_logs = models.ManyToManyField(TaskLog)
    email_task_logs = models.ManyToManyField(
        TaskLog,
        related_name="+",
    )

    """
    Line Manager
    """
    # The manager that processed the Leaver (could be the manager from UK SBS)
    processing_manager_activitystream_user = models.ForeignKey(
        ActivityStreamStaffSSOUser,
        on_delete=models.CASCADE,
        related_name="+",
        blank=True,
        null=True,
    )
    reason_for_leaving = models.CharField(
        choices=ReasonForleaving.choices,
        max_length=255,
        blank=True,
        null=True,
    )
    leaver_paid_unpaid = models.CharField(
        choices=LeaverPaidUnpaid.choices,
        max_length=255,
        blank=True,
        null=True,
    )
    annual_leave = models.CharField(
        choices=AnnualLeavePaidOrDeducted.choices,
        max_length=255,
        blank=True,
        null=True,
    )
    annual_leave_measurement = models.CharField(
        choices=DaysHours.choices,
        max_length=255,
        blank=True,
        null=True,
    )
    annual_number = models.IntegerField(null=True, blank=True)
    flexi_leave = models.CharField(
        choices=FlexiLeavePaidOrDeducted.choices,
        max_length=255,
        blank=True,
        null=True,
    )
    flexi_number = models.IntegerField(null=True, blank=True)

    line_reports = models.JSONField(null=True, blank=True)

    line_manager_complete = models.DateTimeField(null=True, blank=True)

    """
    SRE Access
    """

    vpn_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="vpn_access_task_log",
        null=True,
        blank=True,
    )

    govuk_paas_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="govuk_paas_access_task_log",
        null=True,
        blank=True,
    )

    github_user_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="github_user_task_log",
        null=True,
        blank=True,
    )

    sentry_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="sentry_access_task_log",
        null=True,
        blank=True,
    )

    slack_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="slack_access_task_log",
        null=True,
        blank=True,
    )

    sso_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="sso_access_task_log",
        null=True,
        blank=True,
    )

    aws_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="aws_access_task_log",
        null=True,
        blank=True,
    )

    jira_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="jira_access_task_log",
        null=True,
        blank=True,
    )

    sre_complete = models.DateTimeField(null=True, blank=True)

    """
    Security Team
    """

    security_pass_destroyed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="security_pass_destroyed_task_log",
        null=True,
        blank=True,
    )
    security_pass_not_returned = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="security_pass_not_returned_task_log",
        null=True,
        blank=True,
    )
    security_team_building_pass_complete = models.DateTimeField(null=True, blank=True)

    rosa_kit_form_data = models.JSONField(null=True, blank=True)
    rosa_mobile_returned = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="rosa_mobile_returned_task_log",
        null=True,
        blank=True,
    )
    rosa_laptop_returned = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="rosa_laptop_returned_task_log",
        null=True,
        blank=True,
    )
    rosa_key_returned = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="rosa_key_returned_task_log",
        null=True,
        blank=True,
    )
    security_team_rosa_kit_complete = models.DateTimeField(null=True, blank=True)

    @property
    def security_team_complete(self) -> bool:
        if (
            self.security_team_building_pass_complete
            and self.security_team_rosa_kit_complete
        ):
            return True
        return False

    """
    Methods
    """

    def get_leaving_date(self) -> Optional[datetime]:
        if self.leaving_date:
            return self.leaving_date

        leaver_information: Optional[
            "LeaverInformation"
        ] = self.leaver_information.first()
        if leaver_information and leaver_information.leaving_date:
            return leaver_information.leaving_date
        return None

    def get_last_day(self) -> Optional[datetime]:
        if self.last_day:
            return self.last_day

        leaver_information: Optional[
            "LeaverInformation"
        ] = self.leaver_information.first()
        if leaver_information and leaver_information.last_day:
            return leaver_information.last_day
        return None

    def get_leaver_name(self) -> Optional[str]:
        """
        Get the Leaver's name in order of preference:

        - From the LeaverInformation (This should be up to date info provided by the Leaver)
        - From the Leaver Activity Stream
        """
        leaver_information: Optional[
            "LeaverInformation"
        ] = self.leaver_information.first()
        if leaver_information:
            leaver_info_first_name = leaver_information.leaver_first_name
            leaver_info_last_name = leaver_information.leaver_last_name
            if leaver_info_first_name and leaver_info_last_name:
                return f"{leaver_info_first_name} {leaver_info_last_name}"

        leaver_activitystream_user = self.leaver_activitystream_user
        if leaver_activitystream_user:
            leaver_as_first_name = leaver_activitystream_user.first_name
            leaver_as_last_name = leaver_activitystream_user.last_name
            if leaver_as_first_name and leaver_as_last_name:
                return f"{leaver_as_first_name} {leaver_as_last_name}"

        return None

    def get_leaver_email(self) -> Optional[str]:
        if self.leaver_activitystream_user:
            sso_email: Optional[
                ActivityStreamStaffSSOUserEmail
            ] = self.leaver_activitystream_user.sso_emails.first()
            if sso_email:
                return sso_email.email_address
        return None

    def get_line_manager(self) -> Optional[ActivityStreamStaffSSOUser]:
        """
        Returns the Line Manager that is in use.
        """

        if self.processing_manager_activitystream_user:
            return self.processing_manager_activitystream_user
        if self.manager_activitystream_user:
            return self.manager_activitystream_user
        return None

    def sre_services(self) -> List[Tuple[str, str, bool]]:
        """
        Returns a list of the SRE services and if access has been removed.
        Tuple: (service_field, service_name, access_removed)
        """

        sre_service_label_mapping: List[Tuple[str, str]] = [
            ("vpn_access_removed", "VPN"),
            ("govuk_paas_access_removed", "GOV UK PaaS"),
            ("github_user_access_removed", "Github"),
            ("sentry_access_removed", "Sentry"),
            ("slack_removed", "Slack"),
            ("sso_access_removed", "SSO"),
            ("aws_access_removed", "AWS"),
            ("jira_access_removed", "Jira"),
        ]
        sre_services: List[Tuple[str, str, bool]] = []
        for service_field, service_label in sre_service_label_mapping:
            access_removed: bool = getattr(self, service_field) is not None
            sre_services.append((service_field, service_label, access_removed))
        return sre_services

    def get_security_bp_reminder_email_tasks(self) -> LeavingRequestReminderEmailTasks:
        from leavers.utils.leaving_request import get_email_task_logs
        from leavers.workflow.tasks import SECURITY_TEAM_BP_REMINDER_EMAILS

        email_ids = cast(
            List["EmailIds"],
            [email_id for _, email_id in SECURITY_TEAM_BP_REMINDER_EMAILS.items()],
        )
        email_task_logs = get_email_task_logs(
            leaving_request=self,
            email_ids=email_ids,
        )
        email_tasks: LeavingRequestReminderEmailTasks = {
            "day_after_lwd": [],
            "two_days_after_lwd": [],
            "on_ld": [],
            "one_day_after_ld": [],
            "two_days_after_ld_lm": [],
            "two_days_after_ld_proc": [],
        }
        for key, _ in email_tasks.items():
            email_tasks[key] = email_task_logs[  # type: ignore
                SECURITY_TEAM_BP_REMINDER_EMAILS[key]
            ]
        return email_tasks

    def get_security_rk_reminder_email_tasks(self) -> LeavingRequestReminderEmailTasks:
        from leavers.utils.leaving_request import get_email_task_logs
        from leavers.workflow.tasks import SECURITY_TEAM_RK_REMINDER_EMAILS

        email_ids = cast(
            List["EmailIds"],
            [email_id for _, email_id in SECURITY_TEAM_RK_REMINDER_EMAILS.items()],
        )
        email_task_logs = get_email_task_logs(
            leaving_request=self,
            email_ids=email_ids,
        )
        email_tasks: LeavingRequestReminderEmailTasks = {
            "day_after_lwd": [],
            "two_days_after_lwd": [],
            "on_ld": [],
            "one_day_after_ld": [],
            "two_days_after_ld_lm": [],
            "two_days_after_ld_proc": [],
        }
        for key, _ in email_tasks.items():
            email_tasks[key] = email_task_logs[  # type: ignore
                SECURITY_TEAM_RK_REMINDER_EMAILS[key]
            ]
        return email_tasks

    def get_sre_reminder_email_tasks(self) -> LeavingRequestReminderEmailTasks:
        from leavers.utils.leaving_request import get_email_task_logs
        from leavers.workflow.tasks import SRE_REMINDER_EMAILS

        email_ids = cast(
            List["EmailIds"],
            [email_id for _, email_id in SRE_REMINDER_EMAILS.items()],
        )
        email_task_logs = get_email_task_logs(
            leaving_request=self,
            email_ids=email_ids,
        )
        email_tasks: LeavingRequestReminderEmailTasks = {
            "day_after_lwd": [],
            "two_days_after_lwd": [],
            "on_ld": [],
            "one_day_after_ld": [],
            "two_days_after_ld_lm": [],
            "two_days_after_ld_proc": [],
        }
        for key, _ in email_tasks.items():
            email_tasks[key] = email_task_logs[SRE_REMINDER_EMAILS[key]]  # type: ignore
        return email_tasks


class SlackMessage(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    slack_timestamp = models.CharField(max_length=100)
    channel_id = models.CharField(max_length=100)
    leaving_request = models.ForeignKey(
        LeavingRequest,
        on_delete=models.CASCADE,
        related_name="slack_messages",
    )


class LeaverInformation(models.Model):
    leaving_request = models.ForeignKey(
        LeavingRequest,
        on_delete=models.CASCADE,
        related_name="leaver_information",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updates = models.JSONField()

    last_day = models.DateTimeField(null=True, blank=True)
    leaving_date = models.DateTimeField(null=True, blank=True)

    # Leaver information
    leaver_first_name = models.CharField(max_length=1000, null=True, blank=True)
    leaver_last_name = models.CharField(max_length=1000, null=True, blank=True)
    leaver_date_of_birth = models.DateField(null=True, blank=True)
    personal_email = models.EmailField(null=True, blank=True)
    job_title = models.CharField(max_length=1000, null=True, blank=True)
    directorate_id = models.CharField(max_length=1000, null=True, blank=True)
    staff_id = models.CharField(max_length=1000, null=True, blank=True)

    # Extra information
    has_locker = models.BooleanField(null=True, blank=True)
    has_dse = models.BooleanField(null=True, blank=True)

    # Leaver contact informtion
    contact_phone = models.CharField(max_length=1000, null=True, blank=True)
    contact_address_line_1 = models.CharField(max_length=1000, null=True, blank=True)
    contact_address_line_2 = models.CharField(max_length=1000, null=True, blank=True)
    contact_address_city = models.CharField(max_length=1000, null=True, blank=True)
    contact_address_county = models.CharField(max_length=1000, null=True, blank=True)
    contact_address_postcode = models.CharField(max_length=10, null=True, blank=True)

    # Display Screen Equipment
    dse_assets = models.JSONField(null=True, blank=True)

    # Return Cirrus Kit
    cirrus_assets = models.JSONField(null=True, blank=True)
    information_is_correct = models.BooleanField(null=True)
    additional_information = models.CharField(max_length=1000)
    return_option = models.CharField(
        max_length=10, choices=ReturnOptions.choices, null=True, blank=True
    )
    return_personal_phone = models.CharField(max_length=16, null=True, blank=True)
    return_contact_email = models.EmailField(null=True, blank=True)

    return_address_line_1 = models.CharField(max_length=1000, null=True, blank=True)
    return_address_line_2 = models.CharField(max_length=1000, null=True, blank=True)
    return_address_city = models.CharField(max_length=1000, null=True, blank=True)
    return_address_county = models.CharField(max_length=1000, null=True, blank=True)
    return_address_postcode = models.CharField(max_length=15, null=True, blank=True)

    @property
    def contact_address(self) -> Address:
        return {
            "line_1": self.contact_address_line_1 or "",
            "line_2": self.contact_address_line_2 or "",
            "town_or_city": self.contact_address_city or "",
            "county": self.contact_address_county or "",
            "postcode": self.contact_address_postcode or "",
        }

    @property
    def return_address(self) -> Address:
        return {
            "line_1": self.return_address_line_1 or "",
            "line_2": self.return_address_line_2 or "",
            "town_or_city": self.return_address_city or "",
            "county": self.return_address_county or "",
            "postcode": self.return_address_postcode or "",
        }
