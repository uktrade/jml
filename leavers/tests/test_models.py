from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from leavers.factories import LeaverInformationFactory, LeavingRequestFactory
from leavers.types import StaffType


class TestLeavingRequest(TestCase):
    def test_factory(self):
        leaving_request = LeavingRequestFactory()
        self.assertTrue(leaving_request.pk)

    @freeze_time("2022-12-12 12:00:00")
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
        # 2 weeks, plus 1 day, then another because it's a weekend
        expected_datetime = two_weeks_from_now + timedelta(days=2)

        self.assertEqual(
            leaving_request.get_leaving_date().date(),
            expected_datetime.date(),
        )
        self.assertEqual(
            leaving_request.get_leaving_date().time(),
            expected_datetime.time(),
        )

    @freeze_time("2022-12-12 12:00:00")
    def test_get_last_day(self):
        leaving_request = LeavingRequestFactory()
        self.assertEqual(leaving_request.get_last_day(), None)

        one_week_from_now = timezone.now() + timedelta(days=7)
        LeaverInformationFactory(
            leaving_request=leaving_request,
            last_day=one_week_from_now,
        )
        self.assertEqual(leaving_request.get_last_day(), one_week_from_now)

        two_weeks_from_now = timezone.now() + timedelta(days=14)
        leaving_request.last_day = two_weeks_from_now
        leaving_request.save()
        self.assertEqual(leaving_request.get_last_day(), two_weeks_from_now)

        leaving_request.staff_type = StaffType.BENCH_CONTRACTOR.value
        leaving_request.save()
        # 2 weeks, plus 1 day, then another because it's a weekend
        expected_datetime = two_weeks_from_now + timedelta(days=2)
        self.assertEqual(
            leaving_request.get_last_day().date(),
            expected_datetime.date(),
        )
        self.assertEqual(
            leaving_request.get_last_day().time(),
            expected_datetime.time(),
        )


class TestLeavingInformation(TestCase):
    def test_factory(self):
        leaver_info = LeaverInformationFactory()
        self.assertTrue(leaver_info.pk)
