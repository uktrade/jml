import uuid

from django.contrib.auth import get_user_model
from django.db import models

from activity_stream.models import ActivityStreamStaffSSOUser
from leavers.forms.leaver import ReturnOptions, SecurityClearance


class TaskLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    task_name = models.CharField(max_length=155)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="task_logs",
    )


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
    # We won't necessary have an app user
    leaver_first_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    leaver_last_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    hardware_received = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="hardware_task_log",
        null=True,
        blank=True,
    )

    """
    Task Logs
    """

    task_logs = models.ManyToManyField(TaskLog)

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

    sre_complete = models.BooleanField(default=False)

    """
    Security Team Access
    """

    building_pass_access_revoked = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="building_pass_access_task_log",
        null=True,
        blank=True,
    )

    rosa_access_revoked = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name="rosa_access_task_log",
        null=True,
        blank=True,
    )

    """
    UKSBS PDF data
    """

    uksbs_pdf_data = models.JSONField(null=True, blank=True)

    """
    Line Manager
    """

    security_clearance = models.CharField(
        choices=SecurityClearance.choices,
        max_length=255,
        blank=True,
        null=True,
    )
    is_rosa_user = models.BooleanField(null=True, blank=True)
    holds_government_procurement_card = models.BooleanField(null=True, blank=True)


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

    leaving_date = models.DateTimeField(null=True, blank=True)
    leaver_email = models.EmailField(unique=True)

    # Leaver information
    leaver_first_name = models.CharField(max_length=1000, null=True, blank=True)
    leaver_last_name = models.CharField(max_length=1000, null=True, blank=True)
    personal_email = models.EmailField(null=True, blank=True)
    job_title = models.CharField(max_length=1000, null=True, blank=True)
    directorate_id = models.CharField(max_length=1000, null=True, blank=True)
    staff_id = models.CharField(max_length=1000, null=True, blank=True)

    # Extra information
    locker_number = models.CharField(max_length=1000, null=True, blank=True)
    has_dse = models.BooleanField(null=True, blank=True)

    # Display Screen Equipment
    dse_assets = models.JSONField(null=True, blank=True)

    # Return Cirrus Kit
    cirrus_assets = models.JSONField(null=True, blank=True)
    information_is_correct = models.BooleanField(null=True)
    additional_information = models.CharField(max_length=1000)
    return_option = models.CharField(max_length=10, choices=ReturnOptions.choices)
    return_personal_phone = models.CharField(max_length=16, null=True, blank=True)
    return_contact_email = models.EmailField(null=True, blank=True)
    return_address_building_and_street = models.CharField(
        max_length=1000, null=True, blank=True
    )
    return_address_city = models.CharField(max_length=1000, null=True, blank=True)
    return_address_county = models.CharField(max_length=1000, null=True, blank=True)
    return_address_postcode = models.CharField(max_length=15, null=True, blank=True)

    @property
    def display_address(self) -> str:
        address_data = [
            self.return_address_building_and_street,
            self.return_address_city,
            self.return_address_county,
            self.return_address_postcode,
        ]
        return ", \n".join(filter(None, address_data))
