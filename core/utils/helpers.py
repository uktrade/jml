from datetime import date, datetime
from enum import Enum
from typing import Dict, Iterable, List, Literal, Optional, Type

from django.db.models import Model, QuerySet
from govuk_bank_holidays.bank_holidays import BankHolidays

# 1 January 2022
DATE_FORMAT_STR = "%d %B %Y"
# 1 January 2022 13:24
DATETIME_FORMAT_STR = f"{DATE_FORMAT_STR} %H:%M"


class IsoWeekdays(Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


def bool_to_yes_no(value: Optional[bool] = None) -> Literal["yes", "no"]:
    if value:
        return "yes"
    return "no"


def yes_no_to_bool(value: Literal["yes", "no"]) -> bool:
    if value == "yes":
        return True
    elif value == "no":
        return False
    raise ValueError("Invalid value for yes_no_to_bool")


def make_possessive(word: Optional[str]) -> str:
    if not word:
        return ""
    if word.endswith("s"):
        return word + "'"
    return word + "'s"


def queryset_to_specific(initial_queryset: QuerySet) -> Iterable[Type[Model]]:
    """
    Convert a Queryset to a list of specific models.

    Only use this on an already filtered queryset (after it has been paginated).
    """

    initial_pks = initial_queryset.values_list("pk", flat=True)

    subclasses = initial_queryset.model.__subclasses__()
    subclass_pks: Dict[Type[Model], List[str]] = {}
    subclass_objects: Dict[int, Type[Model]] = {}

    for subclass in subclasses:
        subclass_queryset: QuerySet = subclass.objects.filter(pk__in=initial_pks)
        subclass_objects |= {obj.pk: obj for obj in subclass_queryset}
        subclass_pks[subclass] = subclass_queryset.values_list("pk", flat=True)

    non_subclass_pks = set(initial_pks) - set(subclass_objects.keys())
    non_subclass_objects: Dict[int, Type[Model]] = {
        obj.pk: obj for obj in initial_queryset.filter(pk__in=non_subclass_pks)
    }

    for init_pk in initial_pks:
        if init_pk in non_subclass_pks:
            yield non_subclass_objects[init_pk]
        else:
            yield subclass_objects[init_pk]


def is_work_day_and_time(dt: datetime) -> bool:
    """Returns True if it is a work day and during working hours."""

    bank_holidays = BankHolidays()

    d = dt.date()
    if not bank_holidays.is_work_day(date=d):
        return False

    # Check to see if the time is between 9-5.
    if dt.hour >= 9 and dt.hour < 17 or (dt.hour == 17 and dt.minute == 0):
        return True
    return False


def get_next_workday(d: date) -> date:
    """Returns the next work day."""

    bank_holidays = BankHolidays()
    return bank_holidays.get_next_work_day(date=d)
