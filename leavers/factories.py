import uuid
from datetime import timedelta
from typing import Any, Dict, List

import factory
import factory.fuzzy
from django.utils import timezone
from factory.django import DjangoModelFactory

from activity_stream.factories import ActivityStreamStaffSSOUserFactory
from leavers import models, types
from user.test.factories import UserFactory


class LeavingRequestFactory(DjangoModelFactory):
    class Meta:
        model = models.LeavingRequest

    uuid = uuid.uuid4()
    user_requesting = factory.SubFactory(UserFactory)
    leaver_activitystream_user = factory.SubFactory(ActivityStreamStaffSSOUserFactory)
    manager_activitystream_user = factory.SubFactory(ActivityStreamStaffSSOUserFactory)
    data_recipient_activitystream_user = factory.SubFactory(
        ActivityStreamStaffSSOUserFactory
    )
    line_reports: List[Dict[str, Any]] = []


class SlackMessageFactory(DjangoModelFactory):
    class Meta:
        model = models.SlackMessage

    created_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.now() - timedelta(days=10)
    )
    slack_timestamp = factory.Sequence(lambda n: f"{n}")
    channel_id = factory.Sequence(lambda n: f"channel_{n}")
    leaving_request = factory.SubFactory(LeavingRequestFactory)


class LeaverInformationFactory(DjangoModelFactory):
    class Meta:
        model = models.LeaverInformation

    leaving_request = factory.SubFactory(LeavingRequestFactory)
    updates: types.LeaverDetailUpdates = {}
