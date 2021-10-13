from django.db import models
from django.contrib.auth import get_user_model


class LeavingRequest(models.Model):
    flow = models.OneToOneField(
        "django_workflow_engine.Flow",
        models.CASCADE,
        related_name="leaving_request",
    )

    requested_at = models.DateTimeField(auto_now_add=True)
    requested_by = models.CharField(max_length=255,)  # SSO id
    last_day = models.DateTimeField(null=True, blank=True)
    hardware_received = models.BooleanField(default=False)
    requesting_user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="requesting_users",
        null=True,
        blank=True,
    )
    leaver_user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="leaving_users",
        null=True,
        blank=True,
    )
