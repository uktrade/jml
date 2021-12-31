from datetime import timedelta

import factory
import factory.fuzzy
from django.utils import timezone
from factory.django import DjangoModelFactory

from activity_stream.models import ActivityStreamStaffSSOUser


class ActivityStreamStaffSSOUserFactory(DjangoModelFactory):
    class Meta:
        model = ActivityStreamStaffSSOUser

    identifier = factory.fuzzy.FuzzyText(length=255)  # /PS-IGNORE
    name = factory.fuzzy.FuzzyText(length=255)  # /PS-IGNORE
    obj_type = factory.fuzzy.FuzzyText(length=255)  # /PS-IGNORE
    first_name = factory.fuzzy.FuzzyText(length=255)  # /PS-IGNORE
    last_name = factory.fuzzy.FuzzyText(length=255)  # /PS-IGNORE
    email_address = factory.Sequence(
        lambda n: f"activity_stream_staff_sso_user_{n}@example.com"  # /PS-IGNORE
    )
    user_id = factory.fuzzy.FuzzyText(length=255)  # /PS-IGNORE
    status = factory.fuzzy.FuzzyText(length=255)  # /PS-IGNORE
    last_accessed = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.now() - timedelta(days=10),
    )
    joined = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.now() - timedelta(days=10),
    )
    email_user_id = factory.fuzzy.FuzzyText(length=255)  # /PS-IGNORE
    contact_email_address = factory.Sequence(
        lambda n: f"activity_stream_staff_sso_user_{n}_contact@example.com"  # /PS-IGNORE
    )
    became_inactive_on = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.now() - timedelta(days=10),
    )
    available = True
