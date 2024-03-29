from datetime import datetime

from django.test import TestCase
from django.utils.timezone import make_aware
from freezegun import freeze_time

from leavers.workflow.utils import get_payroll_date, is_x_days_before_payroll


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
        self.assertTrue(is_x_days_before_payroll(2))
        self.assertFalse(is_x_days_before_payroll(1))
        self.assertFalse(is_x_days_before_payroll(0))

    @freeze_time("2021-11-09")
    def test_is_1_day_before_payroll(self):
        self.assertFalse(is_x_days_before_payroll(2))
        self.assertTrue(is_x_days_before_payroll(1))
        self.assertFalse(is_x_days_before_payroll(0))

    @freeze_time("2021-11-10")
    def test_is_day_of_payroll(self):
        self.assertFalse(is_x_days_before_payroll(2))
        self.assertFalse(is_x_days_before_payroll(1))
        self.assertTrue(is_x_days_before_payroll(0))
