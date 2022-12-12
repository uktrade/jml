import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.query import QuerySet

from activity_stream.models import ActivityStreamStaffSSOUser
from core.types import Address
from core.utils.helpers import DATETIME_FORMAT_STR, get_next_workday
from leavers.forms.line_manager import (
    AnnualLeavePaidOrDeducted,
    DaysHours,
    FlexiLeavePaidOrDeducted,
    LeaverPaidUnpaid,
)
from leavers.forms.sre import ServiceAndToolActions
from leavers.types import (
    LeavingReason,
    ReturnOptions,
    SecurityClearance,
    StaffType,
    TaskNote,
)


class TaskLog(models.Model):
    # When the TaskLog was created.
    created_at = models.DateTimeField(auto_now_add=True)
    # A string representation of the action/task.
    task_name = models.CharField(max_length=155)
    # The user the performed the task.
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="task_logs",
        blank=True,
        null=True,
    )
    # A model/field reference to produce a history for a given field.
    reference = models.CharField(max_length=155, blank=True, null=True)
    # An optional string value to store a status of a task.
    value = models.CharField(max_length=155, blank=True, null=True)
    # A string note added to the task.
    notes = models.CharField(max_length=1000, blank=True, null=True)


class LeavingRequest(models.Model):
    class Meta:
        permissions = [
            ("select_leaver", "Can select the user that is leaving"),
        ]

    uuid = models.UUIDField(default=uuid.uuid4)
    flow = models.OneToOneField(
        "django_workflow_engine.Flow",
        models.CASCADE,
        related_name="leaving_request",
        null=True,
        blank=True,
    )

    last_modified = models.DateTimeField(auto_now=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    requested_by = models.CharField(
        max_length=255,
    )  # SSO id
    service_now_offline = models.BooleanField(default=False)

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
        related_name="leaving_requests",
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
        choices=LeavingReason.choices,
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
    annual_number = models.DecimalField(
        decimal_places=2,
        max_digits=7,
        null=True,
        blank=True,
    )
    flexi_leave = models.CharField(
        choices=FlexiLeavePaidOrDeducted.choices,
        max_length=255,
        blank=True,
        null=True,
    )
    flexi_number = models.DecimalField(
        decimal_places=2,
        max_digits=7,
        null=True,
        blank=True,
    )

    line_reports = models.JSONField(null=True, blank=True)

    line_manager_complete = models.DateTimeField(null=True, blank=True)
    line_manager_service_now_complete = models.DateTimeField(null=True, blank=True)

    @property
    def leaver(self) -> ActivityStreamStaffSSOUser:
        return self.leaver_activitystream_user

    @property
    def show_hr_and_payroll(self) -> bool:
        return self.reason_for_leaving != LeavingReason.TRANSFER.value

    @property
    def show_line_reports(self) -> bool:
        return self.reason_for_leaving != LeavingReason.TRANSFER.value

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

    trello_user_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="trello_user_task_log",
        null=True,
        blank=True,
    )

    gitlab_user_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="gitlab_user_task_log",
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
    security_pass_disabled = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="security_pass_disabled_task_log",
        null=True,
        blank=True,
    )
    security_pass_returned = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="security_pass_returned_task_log",
        null=True,
        blank=True,
    )
    security_clearance_status = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="security_clearance_status_task_log",
        null=True,
        blank=True,
    )
    security_clearance_level = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="security_clearance_level_task_log",
        null=True,
        blank=True,
    )
    security_team_building_pass_complete = models.DateTimeField(null=True, blank=True)

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

    """
    Workflow attributes
    """
    manually_offboarded_from_uksbs = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="manually_offboarded_from_uksbs",
        null=True,
        blank=True,
    )

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
        leaving_date: Optional[datetime] = None
        if self.leaving_date:
            leaving_date = self.leaving_date
        else:
            leaver_information: Optional[
                "LeaverInformation"
            ] = self.leaver_information.first()
            if leaver_information and leaver_information.leaving_date:
                leaving_date = leaver_information.leaving_date

        # If the leaver is a bench contractor, the leaving date is 1 workday
        # day after the last day of the contract.
        if leaving_date:
            ld_date = leaving_date.date()
            if self.staff_type == StaffType.BENCH_CONTRACTOR.value:
                new_leaving_date = get_next_workday(ld_date)
                leaving_date = datetime.combine(new_leaving_date, leaving_date.time())

        return leaving_date

    def get_last_day(self) -> Optional[datetime]:
        last_day: Optional[datetime] = None
        if self.last_day:
            last_day = self.last_day
        else:
            leaver_information: Optional[
                "LeaverInformation"
            ] = self.leaver_information.first()
            if leaver_information and leaver_information.last_day:
                last_day = leaver_information.last_day

        # If the leaver is a bench contractor, the last date is 1 workday
        # after the last day of the contract.
        if last_day:
            ld_date = last_day.date()
            if self.staff_type == StaffType.BENCH_CONTRACTOR.value:
                new_last_day = get_next_workday(ld_date)
                last_day = datetime.combine(new_last_day, last_day.time())

        return last_day

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
        leaver_emails = (
            self.leaver_activitystream_user.get_email_addresses_for_contact()
        )
        if not leaver_emails:
            return None
        return leaver_emails[0]

    def get_line_manager(self) -> Optional[ActivityStreamStaffSSOUser]:
        """
        Returns the Line Manager that is in use.
        """

        if self.processing_manager_activitystream_user:
            return self.processing_manager_activitystream_user
        if self.manager_activitystream_user:
            return self.manager_activitystream_user
        return None

    def sre_services(self) -> List[Tuple[str, str, ServiceAndToolActions]]:
        """
        Returns a list of the SRE services and if access has been removed.
        Tuple: (service_field, service_name, access_removed)
        """

        sre_service_label_mapping: List[Tuple[str, str]] = [
            ("aws_access_removed", "AWS"),
            ("github_user_access_removed", "Github"),
            ("gitlab_user_access_removed", "GitLab"),
            ("govuk_paas_access_removed", "GOV UK PaaS"),
            ("jira_access_removed", "Jira"),
            ("sentry_access_removed", "Sentry"),
            ("slack_removed", "Slack"),
            ("trello_user_access_removed", "Trello"),
            ("vpn_access_removed", "VPN"),
        ]
        sre_services: List[Tuple[str, str, ServiceAndToolActions]] = []
        for service_field, service_label in sre_service_label_mapping:
            status: ServiceAndToolActions = ServiceAndToolActions.NOT_STARTED
            service_task_log: Optional[TaskLog] = getattr(self, service_field)
            if service_task_log:
                status = ServiceAndToolActions(service_task_log.value)
            sre_services.append(
                (
                    service_field,
                    service_label,
                    status,
                )
            )
        return sre_services

    def get_sre_notes(self, field_name: str) -> List[TaskNote]:
        sre_notes: List[TaskNote] = []

        field_task_logs: QuerySet[TaskLog] = self.task_logs.filter(
            reference=f"LeavingRequest.{field_name}", notes__isnull=False
        ).order_by("-created_at")
        for field_task_log in field_task_logs:
            full_name = "System"
            if field_task_log.user:
                full_name = field_task_log.user.get_full_name()
            sre_notes.append(
                TaskNote(
                    datetime=field_task_log.created_at.strftime(DATETIME_FORMAT_STR),
                    full_name=full_name,
                    note=field_task_log.notes or "",
                )
            )

        return sre_notes

    def get_security_building_pass_notes(self) -> List[TaskNote]:
        security_building_pass_notes: List[TaskNote] = []

        task_logs: QuerySet[TaskLog] = self.task_logs.filter(
            reference="LeavingRequest.security_team_building_pass_complete",
            notes__isnull=False,
        ).order_by("-created_at")
        for task_log in task_logs:
            full_name = "System"
            if task_log.user:
                full_name = task_log.user.get_full_name()
            security_building_pass_notes.append(
                TaskNote(
                    datetime=task_log.created_at.strftime(DATETIME_FORMAT_STR),
                    full_name=full_name,
                    note=task_log.notes or "",
                )
            )

        return security_building_pass_notes

    def get_security_rosa_kit_notes(self, field_name: str) -> List[TaskNote]:
        security_rosa_kit_notes: List[TaskNote] = []

        security_rosa_kit_reference: str = f"LeavingRequest.{field_name}"

        task_logs: QuerySet[TaskLog] = self.task_logs.filter(
            reference=security_rosa_kit_reference,
            notes__isnull=False,
        ).order_by("-created_at")
        for task_log in task_logs:
            full_name = "System"
            if task_log.user:
                full_name = task_log.user.get_full_name()
            security_rosa_kit_notes.append(
                TaskNote(
                    datetime=task_log.created_at.strftime(DATETIME_FORMAT_STR),
                    full_name=full_name,
                    note=task_log.notes or "",
                )
            )

        return security_rosa_kit_notes


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
    # TODO: Change to a OneToOne relationship.
    leaving_request = models.ForeignKey(
        LeavingRequest,
        on_delete=models.CASCADE,
        related_name="leaver_information",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updates = models.JSONField(default=dict)

    last_day = models.DateTimeField(null=True, blank=True)
    leaving_date = models.DateTimeField(null=True, blank=True)

    # Leaver information
    leaver_first_name = models.CharField(max_length=1000, null=True, blank=True)
    leaver_last_name = models.CharField(max_length=1000, null=True, blank=True)
    leaver_date_of_birth = models.DateField(null=True, blank=True)
    job_title = models.CharField(max_length=1000, null=True, blank=True)

    # Extra information
    has_dse = models.BooleanField(null=True, blank=True)

    # Leaver contact informtion
    contact_phone = models.CharField(max_length=1000, null=True, blank=True)
    personal_email = models.EmailField(null=True, blank=True)
    contact_address_line_1 = models.CharField(max_length=1000, null=True, blank=True)
    contact_address_line_2 = models.CharField(max_length=1000, null=True, blank=True)
    contact_address_city = models.CharField(max_length=1000, null=True, blank=True)
    contact_address_county = models.CharField(max_length=1000, null=True, blank=True)
    contact_address_postcode = models.CharField(max_length=10, null=True, blank=True)

    # Display Screen Equipment
    dse_assets = models.JSONField(null=True, blank=True)

    # Return Cirrus Kit
    cirrus_assets = models.JSONField(null=True, blank=True)
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

    # UNUSED FIELDS
    staff_id = models.CharField(max_length=1000, null=True, blank=True)

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
