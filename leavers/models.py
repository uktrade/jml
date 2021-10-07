from django.db import models


class LeavingRequest(models.Model):
    flow = models.OneToOneField(
        "django_workflow_engine.Flow",
        models.CASCADE,
        related_name="leaving_request",
    )

    requested_at = models.DateTimeField(auto_now_add=True)
    requested_by = models.CharField(max_length=255,)  # SSO id
    for_self = models.BooleanField(default=False)
    leaver_email_address = models.EmailField(null=True, blank=True)
    last_day = models.DateTimeField(null=True, blank=True)
