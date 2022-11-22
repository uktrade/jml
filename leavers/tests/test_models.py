from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from leavers.factories import LeaverInformationFactory, LeavingRequestFactory
from leavers.types import StaffType


class TestLeavingRequest(TestCase):
    def test_factory(self):
        leaving_request = LeavingRequestFactory()
        self.assertTrue(leaving_request.pk)

    def test_get_leaving_date(self):
        leaving_request = LeavingRequestFactory()
        self.assertEqual(leaving_request.get_leaving_date(), None)

        one_week_from_now = timezone.now() + timedelta(days=7)
        LeaverInformationFactory(
            leaving_request=leaving_request,
            leaving_date=one_week_from_now,
        )
        self.assertEqual(leaving_request.get_leaving_date(), one_week_from_now)

        two_weeks_from_now = timezone.now() + timedelta(days=14)
        leaving_request.leaving_date = two_weeks_from_now
        leaving_request.save()
        self.assertEqual(leaving_request.get_leaving_date(), two_weeks_from_now)

        leaving_request.staff_type = StaffType.BENCH_CONTRACTOR.value
        leaving_request.save()
        self.assertEqual(
            leaving_request.get_leaving_date(), two_weeks_from_now + timedelta(days=1)
        )


class TestLeavingInformation(TestCase):
    def test_factory(self):
        leaver_info = LeaverInformationFactory()
        self.assertTrue(leaver_info.pk)
