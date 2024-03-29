from datetime import date, timedelta

from govuk_bank_holidays.bank_holidays import BankHolidays

# In UKSBS, the Payroll cut off is 3rd of each month.
# if not a working day, it is the last Friday before the 3rd.
# The cut off is the last day when changes to the current month payroll are accepted
PAY_CUT_OFF_DAY = 3  # The third of the month is the designated cut off date
ALTERNATIVE_WEEK_DAY_DESIGNATED = 4  # Friday

# We need to inform HR that there are incomplete leaver requests
# when we are approaching the payroll cut off date
# The period when we inform HR is starting 4 working days before the cut off date
PAY_CUT_OFF_INTERVAL = -4
DECEMBER = 12
JANUARY = 1


def calculate_working_day_date(start_date: date, working_day_delta: int) -> date:
    """It calculates the date of a working day
    separated from a given date by <working_day_delta> working day
    for instance, to find the next working day from today, use
    calculate_working_day_date(today_date, 1)
    It takes into account bank holidays and weekend to calculate the new date.
    The start date could be a weekend or a bankholiday"""
    bank_holidays = BankHolidays()
    area = BankHolidays.ENGLAND_AND_WALES
    new_date = start_date
    if working_day_delta == 0:
        raise Exception("Invalid value for calculating working day")
    if working_day_delta < 0:
        increment = -1
        delta = -working_day_delta
    else:
        increment = 1
        delta = working_day_delta
    while delta != 0:
        new_date += timedelta(increment)
        if bank_holidays.is_work_day(new_date, division=area):
            delta -= 1
    return new_date


def pay_cut_off_date(month: int, year: int) -> date:
    # Payroll cut off is 3rd of each month,
    # if not a working day, the last friday before the 3rd.
    bank_holidays = BankHolidays()
    area = BankHolidays.ENGLAND_AND_WALES
    cut_off_day = date(year, month, PAY_CUT_OFF_DAY)
    if bank_holidays.is_work_day(cut_off_day, division=area):
        return cut_off_day

    # Find the designated date, in this case the previous Friday
    cut_off_day_of_week = cut_off_day.weekday()
    # Find out how many days away from the alternative designated day we are
    days = cut_off_day_of_week - ALTERNATIVE_WEEK_DAY_DESIGNATED
    if days <= 0:
        # We need to find a date BEFORE the calculated one
        # so if the difference we got is negative,
        # we would end up with a date in the future
        # add 7 to avoid it
        # For instance, if the 3rd of the month is on a Friday (days difference would be 0),
        # and it is a Bankholiday, we need to return the date of the previous Friday.
        # This case can happen if Easter in on the 5th April, as it would be in 2026
        days += 7
    cut_off_day -= timedelta(days)
    # If the previous designated day is also a bankholiday,
    # return the previous working day
    while not bank_holidays.is_work_day(cut_off_day, division=area):
        cut_off_day -= timedelta(-1)
    return cut_off_day


def is_date_within_payroll_cut_off_interval(date_to_check: date) -> tuple[bool, date]:
    """
    It returns True if the date is in the predefined period
    before the payroll cut off date, and the system must notify HR
    """
    bank_holidays = BankHolidays()
    area = BankHolidays.ENGLAND_AND_WALES
    if not bank_holidays.is_work_day(date_to_check, division=area):
        # Ignore non working days
        return False, date_to_check

    month_to_check = date_to_check.month
    year_to_check = date_to_check.year

    # Find the payroll cut off date for the same month
    cut_off_end_date = pay_cut_off_date(month_to_check, year_to_check)
    # If the date to check is after the same month payroll, lets check against
    # next month
    if date_to_check > cut_off_end_date:
        # Find the payroll cut off date for the next month
        if month_to_check != DECEMBER:
            next_month = month_to_check + 1
        else:
            # Special case for December
            next_month = JANUARY
            year_to_check += 1
        cut_off_end_date = pay_cut_off_date(next_month, year_to_check)
    cut_off_start_date = calculate_working_day_date(
        cut_off_end_date, PAY_CUT_OFF_INTERVAL
    )
    if cut_off_start_date <= date_to_check <= cut_off_end_date:
        return True, cut_off_end_date

    return False, date_to_check


def get_next_payroll_cut_off_date(date_to_check: date) -> date:
    """Get the next payroll cut off date after the given date."""
    if date_to_check.day <= PAY_CUT_OFF_DAY:
        # Payroll cut off has not happened yet.
        payroll_cut_off_date = pay_cut_off_date(date_to_check.month, date_to_check.year)
        # If the cut off date for this month has passed, then we need to check the next month.
        if date_to_check.day <= payroll_cut_off_date.day:
            return payroll_cut_off_date

    # Payroll cut off has happened already, so we need to check the next month.
    if date_to_check.month == DECEMBER:
        # Special case for December
        return pay_cut_off_date(JANUARY, date_to_check.year + 1)

    next_month = date_to_check.month + 1 if date_to_check.month < 12 else 1
    return pay_cut_off_date(next_month, date_to_check.year)
