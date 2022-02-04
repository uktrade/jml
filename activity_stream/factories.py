from datetime import timedelta

import factory
import factory.fuzzy
from django.utils import timezone
from factory.django import DjangoModelFactory

from activity_stream.models import ActivityStreamStaffSSOUser


class ActivityStreamStaffSSOUserFactory(DjangoModelFactory):
    class Meta:
        model = ActivityStreamStaffSSOUser

    identifier = factory.fuzzy.FuzzyText(length=255)
    name = factory.fuzzy.FuzzyText(length=255)
    obj_type = factory.fuzzy.FuzzyText(length=255)
    first_name = factory.fuzzy.FuzzyText(length=255)
    last_name = factory.fuzzy.FuzzyText(length=255)
    email_address = factory.Sequence(
        lambda n: f"activity_stream_staff_sso_user_{n}@example.com"  # /PS-IGNORE
    )
    user_id = factory.fuzzy.FuzzyText(length=255)
    status = factory.fuzzy.FuzzyText(length=255)
    last_accessed = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.now() - timedelta(days=10),
    )
    joined = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.now() - timedelta(days=10),
    )
    email_user_id = factory.fuzzy.FuzzyText(length=255)
    contact_email_address = factory.Sequence(
        lambda n: f"activity_stream_staff_sso_user_{n}_contact@example.com"  # /PS-IGNORE
    )
    became_inactive_on = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.now() - timedelta(days=10),
    )
    available = True
