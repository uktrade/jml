from typing import List, Optional

from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Manager
from django.db.models.query import QuerySet


class ActivityStreamStaffSSOUserQuerySet(models.QuerySet):
    def available(self):
        return self.filter(available=True)

    def with_emails(self):
        return self.annotate(
            emails=ArrayAgg("sso_emails__email_address", distinct=True),
        )


ActivityStreamStaffSSOUserManager: Manager[
    "ActivityStreamStaffSSOUser"
] = models.Manager.from_queryset(ActivityStreamStaffSSOUserQuerySet)


class ActivityStreamStaffSSOUser(models.Model):
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

    # These fields come from the people_data data source.
    # NEVER EXPOSE THIS FIELD
    uksbs_person_id = models.CharField(max_length=255)
    uksbs_person_id_override = models.CharField(null=True, blank=True, max_length=255)
    employee_numbers = ArrayField(models.CharField(max_length=255), default=list)

    # Service Now
    service_now_user_id = models.CharField(max_length=255, unique=True, null=True)
    service_now_email_address = models.EmailField(
        max_length=255, unique=True, null=True
    )

    # Used to denote if the user is still returned by the ActivityStream API.
    available = models.BooleanField(default=False)

    objects = ActivityStreamStaffSSOUserManager()

    def __str__(self):
        return self.name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_primary_email(self) -> Optional[str]:
        primary_emails: QuerySet[
            ActivityStreamStaffSSOUserEmail
        ] = self.sso_emails.filter(is_primary=True)
        primary_email = primary_emails.first()
        if primary_email:
            return primary_email.email_address
        return None

    def get_email_addresses_for_contact(self) -> List[str]:
        """
        Return all known emails for this user.

        If the user has a primary email set, only return that.
        """

        primary_email = self.get_primary_email()
        if primary_email:
            return [primary_email]

        emails = set()

        if self.contact_email_address:
            emails.add(self.contact_email_address)

        for sso_email in self.sso_emails.all():
            emails.add(sso_email.email_address)
        return list(emails)

    def get_person_id(self) -> str:
        if self.uksbs_person_id_override:
            return self.uksbs_person_id_override
        return self.uksbs_person_id


class ActivityStreamStaffSSOUserEmail(models.Model):
    # TODO: Remove type ignore comments once the following PR has been merged and
    # upgraded to (https://github.com/typeddjango/django-stubs/pull/1030).
    staff_sso_user = models.ForeignKey(
        ActivityStreamStaffSSOUser,  # type: ignore
        on_delete=models.CASCADE,  # type: ignore
        related_name="sso_emails",
    )  # type: ignore
    email_address = models.EmailField(  # type: ignore
        max_length=255,
    )
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["staff_sso_user", "email_address"],
                name="unique_sso_user_email_address",
            ),
        ]
