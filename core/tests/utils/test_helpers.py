from datetime import date

from django.db.models.query import QuerySet
from django.test import TestCase
from django.utils import timezone

from asset_registry.models import Asset, PhysicalAsset, SoftwareAsset
from core.utils.helpers import (
    bool_to_yes_no,
    get_next_workday,
    is_work_day_and_time,
    make_possessive,
)


class BoolToYesNo(TestCase):
    def test_true(self):
        self.assertEqual(bool_to_yes_no(True), "yes")

    def test_false(self):
        self.assertEqual(bool_to_yes_no(False), "no")

    def test_not_boolean(self):
        self.assertEqual(bool_to_yes_no(""), "no")


class MakePossessive(TestCase):
    def test_simple(self):
        self.assertEqual(make_possessive("Bill"), "Bill's")  # /PS-IGNORE

    def test_ends_in_s(self):
        self.assertEqual(make_possessive("Thomas"), "Thomas'")  # /PS-IGNORE


class IsWorkDayAndTime(TestCase):
    def test_saturday(self):
        self.assertFalse(is_work_day_and_time(timezone.datetime(2022, 11, 26, 12, 30)))

    def test_sunday(self):
        self.assertFalse(is_work_day_and_time(timezone.datetime(2022, 11, 27, 12, 30)))

    def test_monday(self):
        self.assertFalse(is_work_day_and_time(timezone.datetime(2022, 11, 28, 8, 30)))
        self.assertTrue(is_work_day_and_time(timezone.datetime(2022, 11, 28, 9, 00)))
        self.assertTrue(is_work_day_and_time(timezone.datetime(2022, 11, 28, 12, 30)))
        self.assertTrue(is_work_day_and_time(timezone.datetime(2022, 11, 28, 17, 00)))
        self.assertFalse(is_work_day_and_time(timezone.datetime(2022, 11, 28, 17, 30)))

    def test_tuesday(self):
        self.assertFalse(is_work_day_and_time(timezone.datetime(2022, 11, 29, 8, 30)))
        self.assertTrue(is_work_day_and_time(timezone.datetime(2022, 11, 29, 9, 00)))
        self.assertTrue(is_work_day_and_time(timezone.datetime(2022, 11, 29, 12, 30)))
        self.assertTrue(is_work_day_and_time(timezone.datetime(2022, 11, 29, 17, 00)))
        self.assertFalse(is_work_day_and_time(timezone.datetime(2022, 11, 29, 17, 30)))

    def test_wednesday(self):
        self.assertFalse(is_work_day_and_time(timezone.datetime(2022, 11, 30, 8, 30)))
        self.assertTrue(is_work_day_and_time(timezone.datetime(2022, 11, 30, 9, 00)))
        self.assertTrue(is_work_day_and_time(timezone.datetime(2022, 11, 30, 12, 30)))
        self.assertTrue(is_work_day_and_time(timezone.datetime(2022, 11, 30, 17, 00)))
        self.assertFalse(is_work_day_and_time(timezone.datetime(2022, 11, 30, 17, 30)))

    def test_thursday(self):
        self.assertFalse(is_work_day_and_time(timezone.datetime(2022, 12, 1, 8, 30)))
        self.assertTrue(is_work_day_and_time(timezone.datetime(2022, 12, 1, 9, 00)))
        self.assertTrue(is_work_day_and_time(timezone.datetime(2022, 12, 1, 12, 30)))
        self.assertTrue(is_work_day_and_time(timezone.datetime(2022, 12, 1, 17, 00)))
        self.assertFalse(is_work_day_and_time(timezone.datetime(2022, 12, 1, 17, 30)))

    def test_friday(self):
        self.assertFalse(is_work_day_and_time(timezone.datetime(2022, 12, 2, 8, 30)))
        self.assertTrue(is_work_day_and_time(timezone.datetime(2022, 12, 2, 9, 00)))
        self.assertTrue(is_work_day_and_time(timezone.datetime(2022, 12, 2, 12, 30)))
        self.assertTrue(is_work_day_and_time(timezone.datetime(2022, 12, 2, 17, 00)))
        self.assertFalse(is_work_day_and_time(timezone.datetime(2022, 12, 2, 17, 30)))


class GetNextWorkday(TestCase):
    def test_midweek(self):
        self.assertEqual(get_next_workday(date(2022, 11, 22)), date(2022, 11, 23))

    def test_friday(self):
        self.assertEqual(get_next_workday(date(2022, 11, 25)), date(2022, 11, 28))

    def test_saturday(self):
        self.assertEqual(get_next_workday(date(2022, 11, 26)), date(2022, 11, 28))

    def test_sunday(self):
        self.assertEqual(get_next_workday(date(2022, 11, 27)), date(2022, 11, 28))
