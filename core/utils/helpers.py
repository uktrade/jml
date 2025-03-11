from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional

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
