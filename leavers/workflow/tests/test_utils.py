from datetime import datetime
from django.test import TestCase
from django.utils.timezone import make_aware
from freezegun import freeze_time

from leavers.factories import LeavingRequestFactory
from leavers.workflow.utils import get_payroll_date, is_x_days_before_payroll, is_it_leaving_date_plus_x_days


class GetPayrollDate(TestCase):

    @freeze_time("2021-11-01")
    def test_payroll_in_future(self):
        self.assertEqual(get_payroll_date(), make_aware(datetime(2021, 11, 10)))

    @freeze_time("2021-11-11")
    def test_payroll_in_past(self):
        self.assertEqual(get_payroll_date(), make_aware(datetime(2021, 12, 10)))

    @freeze_time("2021-11-10")
    def test_payroll_today(self):
        self.assertEqual(get_payroll_date(), make_aware(datetime(2021, 11, 10)))

    @freeze_time("2021-12-20")
    def test_payroll_next_year(self):
        self.assertEqual(get_payroll_date(), make_aware(datetime(2022, 1, 10)))


class DaysBeforePayroll(TestCase):

    @freeze_time("2021-11-08")
    def test_is_2_days_before_payroll(self):
        self.assertTrue(
            is_x_days_before_payroll(2)
        )
        self.assertFalse(
            is_x_days_before_payroll(1)
        )
        self.assertFalse(
            is_x_days_before_payroll(0)
        )

    @freeze_time("2021-11-09")
    def test_is_1_day_before_payroll(self):
        self.assertFalse(
            is_x_days_before_payroll(2)
        )
        self.assertTrue(
            is_x_days_before_payroll(1)
        )
        self.assertFalse(
            is_x_days_before_payroll(0)
        )
    
    @freeze_time("2021-11-10")
    def test_is_day_of_payroll(self):
        self.assertFalse(
            is_x_days_before_payroll(2)
        )
        self.assertFalse(
            is_x_days_before_payroll(1)
        )
        self.assertTrue(
            is_x_days_before_payroll(0)
        )


class LeavingDatePlusXDays(TestCase):

    def setUp(self):
        self.leaving_date = LeavingRequestFactory(
            last_day=datetime(2021, 12, 1),
        )

    def test_leaving_date_not_set(self):
        # Remove the last day value
        self.leaving_date.last_day = None
        self.leaving_date.save()

        self.assertFalse(is_it_leaving_date_plus_x_days(
            leaving_request=self.leaving_date,
            days_after_leaving_date=1,
        ))

    @freeze_time("2021-11-30")
    def test_leaving_date_tomorrow(self):
        self.assertFalse(is_it_leaving_date_plus_x_days(
            leaving_request=self.leaving_date,
            days_after_leaving_date=1,
        ))
        self.assertFalse(is_it_leaving_date_plus_x_days(
            leaving_request=self.leaving_date,
            days_after_leaving_date=0,
        ))
        self.assertTrue(is_it_leaving_date_plus_x_days(
            leaving_request=self.leaving_date,
            days_after_leaving_date=-1,
        ))

    @freeze_time("2021-12-01")
    def test_leaving_date_today(self):
        self.assertFalse(is_it_leaving_date_plus_x_days(
            leaving_request=self.leaving_date,
            days_after_leaving_date=1,
        ))
        self.assertTrue(is_it_leaving_date_plus_x_days(
            leaving_request=self.leaving_date,
            days_after_leaving_date=0,
        ))
        self.assertFalse(is_it_leaving_date_plus_x_days(
            leaving_request=self.leaving_date,
            days_after_leaving_date=-1,
        ))

    @freeze_time("2021-12-02")
    def test_leaving_date_yesterday(self):
        self.assertTrue(is_it_leaving_date_plus_x_days(
            leaving_request=self.leaving_date,
            days_after_leaving_date=1,
        ))
        self.assertFalse(is_it_leaving_date_plus_x_days(
            leaving_request=self.leaving_date,
            days_after_leaving_date=0,
        ))
        self.assertFalse(is_it_leaving_date_plus_x_days(
            leaving_request=self.leaving_date,
            days_after_leaving_date=-1,
        ))
