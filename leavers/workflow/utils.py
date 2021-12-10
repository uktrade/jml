from datetime import datetime, timedelta
from django.utils import timezone

from leavers.models import LeavingRequest


# Payroll is always the 10th of the month.
PAYROLL_DAY_OF_MONTH = 10


def get_payroll_date() -> datetime:
    today = timezone.now()
    if today.day == PAYROLL_DAY_OF_MONTH:
        # Payroll is today.
        return today

    if today.day < PAYROLL_DAY_OF_MONTH:
        # Payroll hasn't happened this month.
        return today.replace(day=PAYROLL_DAY_OF_MONTH)

    # Payroll is next month.
    payroll_day = PAYROLL_DAY_OF_MONTH
    payroll_month = today.month + 1
    payroll_year = today.year

    # If the month + 1 is 13 we need to set to January of the next year.
    if payroll_month == 13:
        payroll_month = 1
        payroll_year = today.year + 1

    return timezone.make_aware(
        datetime(
            payroll_year,
            payroll_month,
            payroll_day,
        )
    )


def is_x_days_before_payroll(days_before_payroll: int) -> bool:
    payroll_date = get_payroll_date().date()
    x_days_before_payroll = payroll_date - timedelta(days=days_before_payroll)
    today = timezone.now().date()
    return bool(today == x_days_before_payroll)


def is_it_leaving_date_plus_x_days(
    leaving_request: LeavingRequest, days_after_leaving_date: int
) -> bool:
    # If there isn't a last_day set, it can't be past it.
    if not leaving_request.last_day:
        return False

    # Get the date X days after the last_day.
    leaving_date = timezone.make_aware(leaving_request.last_day).date()
    leaving_date_plus_x_days = leaving_date + timedelta(days=days_after_leaving_date)

    # Check to see if the last_day is X days in the past.
    today = timezone.now().date()
    return bool(today == leaving_date_plus_x_days)
