import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from activity_stream.models import ActivityStreamStaffSSOUser
from user.groups import GroupName


class User(AbstractUser):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sso_legacy_user_id"], name="unique_sso_legacy_user_id"
            ),
        ]

    email = models.EmailField(
        unique=True,
        max_length=254,
        verbose_name="email address",
    )

    sso_contact_email = models.EmailField(
        blank=True,
        null=True,
    )
    sso_legacy_user_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    sso_email_user_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    user_id = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def is_in_group(self, group_name: GroupName) -> bool:
        return self.groups.filter(name=group_name.value).exists()

    def get_sso_user(self) -> ActivityStreamStaffSSOUser:
        return ActivityStreamStaffSSOUser.objects.active().get(
            email_user_id=self.sso_email_user_id,
        )
