from django.db import models


class ActivityStreamStaffSSOUserManager(models.Manager):
    def available(self):
        return self.filter(available=True)


class ActivityStreamStaffSSOUser(models.Model):
    # TODO: Remove any fields that contain data we don't need.
    identifier = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    obj_type = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255)  # Legacy SSO id
    status = models.CharField(max_length=255)
    last_accessed = models.DateTimeField(null=True, blank=True)
    joined = models.DateTimeField()
    email_user_id = models.CharField(max_length=255)  # Current SSO id
    contact_email_address = models.EmailField(null=True, max_length=255)
    became_inactive_on = models.DateTimeField(null=True)
    uksbs_person_id = models.CharField(max_length=255)

    # Used to denote if the user is still returned by the ActivityStream API.
    available = models.BooleanField(default=False)

    objects = ActivityStreamStaffSSOUserManager()

    def __str__(self):
        return self.name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class ActivityStreamStaffSSOUserEmail(models.Model):
    staff_sso_user = models.ForeignKey(
        ActivityStreamStaffSSOUser,
        on_delete=models.CASCADE,
        related_name="sso_emails",
    )
    email_address = models.EmailField(
        unique=True,
        max_length=255,
    )


class ServiceEmailAddress(models.Model):
    staff_sso_user = models.ForeignKey(
        ActivityStreamStaffSSOUser,
        on_delete=models.CASCADE,
        related_name="service_emails",
    )
    service_now_email_address = models.EmailField(
        unique=True,
        max_length=255,
    )
