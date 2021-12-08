from django.db import models


class ActivityStreamStaffSSOUser(models.Model):
    # TODO: Remove any fields that contain data we don't need.
    identifier = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    obj_type = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email_address = models.EmailField(max_length=255)
    user_id = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    last_accessed = models.DateTimeField()
    joined = models.DateTimeField()
    email_user_id = models.CharField(max_length=255)
    contact_email_address = models.EmailField(null=True, max_length=255)
    became_inactive_on = models.DateTimeField(null=True)
