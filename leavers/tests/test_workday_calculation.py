from datetime import date

from django.test import TestCase

from leavers.utils.workday_calculation import (
    calculate_working_day_date,
    get_next_payroll_cut_off_date,
    is_date_within_payroll_cut_off_interval,
    pay_cut_off_date,
)

"""
New Year’s Day is on 2023-01-02
Good Friday is on 2023-04-07
Easter Monday is on 2023-04-10
Early May bank holiday is on 2023-05-01
Bank holiday for the coronation of King Charles III is on 2023-05-08
Spring bank holiday is on 2023-05-29
Summer bank holiday is on 2023-08-28
Christmas Day is on 2023-12-25
Boxing Day is on 2023-12-26

"""


class TestWorkDayCalculation(TestCase):
    def test_add_working_day(self):
        # start on a Monday
        test_date = date(2023, 1, 9)
        self.assertEqual(calculate_working_day_date(test_date, 1), date(2023, 1, 10))
        self.assertEqual(calculate_working_day_date(test_date, 2), date(2023, 1, 11))
        self.assertEqual(calculate_working_day_date(test_date, 3), date(2023, 1, 12))
        self.assertEqual(calculate_working_day_date(test_date, 4), date(2023, 1, 13))
        # Exclude weekend
        self.assertEqual(calculate_working_day_date(test_date, 5), date(2023, 1, 16))
        # Go backward
        self.assertEqual(calculate_working_day_date(test_date, -1), date(2023, 1, 6))
        self.assertEqual(calculate_working_day_date(test_date, -2), date(2023, 1, 5))
        self.assertEqual(calculate_working_day_date(test_date, -3), date(2023, 1, 4))
        self.assertEqual(calculate_working_day_date(test_date, -4), date(2023, 1, 3))
        # Across weekend and bankholiday
        self.assertEqual(calculate_working_day_date(test_date, -5), date(2022, 12, 30))

    def test_easter_friday(self):
        good_friday = date(2023, 4, 7)
        day_before_easter = date(2023, 4, 6)
        working_day_after_easter = calculate_working_day_date(day_before_easter, 1)
        self.assertEqual(working_day_after_easter, date(2023, 4, 11))
        self.assertEqual(
            calculate_working_day_date(working_day_after_easter, -1), day_before_easter
        )
        working_day_after_good_friday = calculate_working_day_date(good_friday, 1)
        self.assertEqual(working_day_after_good_friday, date(2023, 4, 11))

    def test_spring_bankholiday(self):
        # Spring bankholiday is on 2023-05-29
        working_day_after_bh = calculate_working_day_date(date(2023, 4, 28), 1)
        self.assertEqual(working_day_after_bh, date(2023, 5, 2))

    def test_spring_and_coronation_bankholiday(self):
        # Spring bankholiday is on 2023-05-29
        # Coronation bankholiday is on 2023-05-08
        working_day_after_bh = calculate_working_day_date(date(2023, 4, 28), 6)
        # Correctly skipped the weekend and the two bankholiday
        self.assertEqual(working_day_after_bh, date(2023, 5, 10))


class TestIsDateWithinPayrollCutOffInterval(TestCase):
    def test_jan_2023(self):
        is_within, _ = is_date_within_payroll_cut_off_interval(date(2022, 12, 30))
        self.assertTrue(is_within)
        # Sunday, so we don't consider it in the cut off period
        is_within, _ = is_date_within_payroll_cut_off_interval(date(2023, 1, 1))
        self.assertFalse(is_within)
        # Bankholiday, so we don't consider it in the cut off period
        is_within, _ = is_date_within_payroll_cut_off_interval(date(2023, 1, 2))
        self.assertFalse(is_within)
        is_within, _ = is_date_within_payroll_cut_off_interval(date(2023, 1, 3))
        self.assertTrue(is_within)
        is_within, _ = is_date_within_payroll_cut_off_interval(date(2023, 1, 4))
        self.assertFalse(is_within)


class TestPayCutOffDate(TestCase):
    def test_2023(self):
        self.assertEqual(pay_cut_off_date(1, 2023), date(2023, 1, 3))
        self.assertEqual(pay_cut_off_date(2, 2023), date(2023, 2, 3))
        self.assertEqual(pay_cut_off_date(3, 2023), date(2023, 3, 3))
        self.assertEqual(pay_cut_off_date(4, 2023), date(2023, 4, 3))
        self.assertEqual(pay_cut_off_date(5, 2023), date(2023, 5, 3))
        # 3rd June is on Saturday
        self.assertEqual(pay_cut_off_date(6, 2023), date(2023, 6, 2))
        self.assertEqual(pay_cut_off_date(7, 2023), date(2023, 7, 3))
        self.assertEqual(pay_cut_off_date(8, 2023), date(2023, 8, 3))
        # 3rd September on Sunday
        self.assertEqual(pay_cut_off_date(9, 2023), date(2023, 9, 1))
        self.assertEqual(pay_cut_off_date(10, 2023), date(2023, 10, 3))
        self.assertEqual(pay_cut_off_date(11, 2023), date(2023, 11, 3))
        # 3rd December on Sunday
        self.assertEqual(pay_cut_off_date(12, 2023), date(2023, 12, 1))


# get_next_payroll_cut_off_date
class TestGetNextPayrollCutOffDate(TestCase):
    def test_1_jan_2023(self):
        self.assertEqual(
            get_next_payroll_cut_off_date(date(2023, 1, 1)),
            date(2023, 1, 3),
        )

    def test_2_jan_2023(self):
        self.assertEqual(
            get_next_payroll_cut_off_date(date(2023, 1, 2)),
            date(2023, 1, 3),
        )

    def test_3_jan_2023(self):
        self.assertEqual(
            get_next_payroll_cut_off_date(date(2023, 1, 3)),
            date(2023, 1, 3),
        )

    def test_4_jan_2023(self):
        self.assertEqual(
            get_next_payroll_cut_off_date(date(2023, 1, 4)),
            date(2023, 2, 3),
        )

    def test_1_jun_2023(self):
        self.assertEqual(
            get_next_payroll_cut_off_date(date(2023, 6, 1)),
            date(2023, 6, 2),
        )

    def test_2_jun_2023(self):
        self.assertEqual(
            get_next_payroll_cut_off_date(date(2023, 6, 2)),
            date(2023, 6, 2),
        )

    def test_3_jun_2023(self):
        self.assertEqual(
            get_next_payroll_cut_off_date(date(2023, 6, 3)),
            date(2023, 7, 3),
        )

    def test_4_jun_2023(self):
        self.assertEqual(
            get_next_payroll_cut_off_date(date(2023, 6, 4)),
            date(2023, 7, 3),
        )
