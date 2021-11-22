import uuid

from django.db import models
from django.contrib.auth import get_user_model


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
    requested_by = models.CharField(max_length=255,)  # SSO id
    last_day = models.DateTimeField(null=True, blank=True)

    user_requesting = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="requesting_users",
    )
    # user_leaving = models.ForeignKey(
    #     get_user_model(),
    #     on_delete=models.CASCADE,
    #     related_name="leaving_users",
    #     null=True,
    #     blank=True,
    # )
    leaver_sso_id = models.CharField(max_length=155)

    hardware_received = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name='hardware_task_log',
        null=True,
        blank=True,
    )

    vpn_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name='vpn_access_task_log',
        null=True,
        blank=True,
    )

    govuk_paas_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name='govuk_paas_access_task_log',
        null=True,
        blank=True,
    )

    github_user_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name='github_user_task_log',
        null=True,
        blank=True,
    )

    sentry_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name='sentry_access_task_log',
        null=True,
        blank=True,
    )

    slack_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name='slack_access_task_log',
        null=True,
        blank=True,
    )

    sso_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name='sso_access_task_log',
        null=True,
        blank=True,
    )

    aws_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name='aws_access_task_log',
        null=True,
        blank=True,
    )

    jira_access_removed = models.OneToOneField(
        TaskLog,
        on_delete=models.CASCADE,
        related_name='jira_access_task_log',
        null=True,
        blank=True,
    )


class SlackMessage(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    slack_timestamp = models.CharField(max_length=100)
    channel_id = models.CharField(max_length=100)
    leaving_request = models.ForeignKey(
        LeavingRequest,
        on_delete=models.CASCADE,
        related_name="slack_messages",
    )
