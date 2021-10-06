from django.db import models


class Position(models.Model):
    title = models.CharField(max_length=50)

    def __str__(self):
        return self.title


class LeavingRequest(models.Model):
    requested_at = models.DateTimeField(auto_now_add=True)
    requested_by = models.CharField(max_length=255,)  # SSO id
    for_self = models.BooleanField()
    leaver_email_address = models.EmailField(null=True, blank=True)
    last_day = models.DateTimeField()
