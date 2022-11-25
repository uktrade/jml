from datetime import date, timedelta
from govuk_bank_holidays.bank_holidays import BankHolidays

# In UKBS, the Payroll cutoff is 3rd of each month.
# if not a working day, it is the last Friday before the 3rd.
# The cutoff is the last day when changes to the current month payroll are accepted
PAY_CUT_OFF_DAY = 3  # The third of the month is the designated cutoff date
ALTERNATIVE_WEEK_DAY_DESIGNATED = 4  # Friday

# We need to inform HR that there are incomplete leaver requests
# when we are approaching the payroll cutoff date
# The period when we inform HR is starting 4 working days before the cutoff date
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
    # Payroll cutoff is 3rd of each month,
    # if not a working day, the last friday before the 3rd.
    bank_holidays = BankHolidays()
    area = BankHolidays.ENGLAND_AND_WALES
    cutoff_day = date(year, month, PAY_CUT_OFF_DAY)
    if bank_holidays.is_work_day(cutoff_day, division=area):
        return cutoff_day

    # Find the designated date, in this case the previous Friday
    cut_off_day_of_week = cutoff_day.weekday()
    # Find out how many days away from the alternative designated day we are
    days = cut_off_day_of_week - ALTERNATIVE_WEEK_DAY_DESIGNATED
    # We need to find a date BEFORE the calculated one
    # so if the difference we got is negative, we would end up with a date in the future
    # add 7 to avoid it
    # For instance, if the 3rd of the month is on a Friday (days difference would be 0),
    # and it is a Bankholiday, we need to return the date of the previous Friday.
    # This case can happen if Easter in on the 5th April, as it would be in 2026
    if days <= 0:
        days += 7
    cutoff_day -= timedelta(days)
    # If the previous designated day is also a bankholiday,
    # return the previous working day
    while not bank_holidays.is_work_day(cutoff_day, division=area):
        cutoff_day -= timedelta(-1)
    return cutoff_day


def is_date_within_payroll_cutoff_interval(date_to_check: date) -> bool:
    """
    It returns True if the date is in the predefined period
    before the payroll cutoff date, and the system must notify HR
    """
    bank_holidays = BankHolidays()
    area = BankHolidays.ENGLAND_AND_WALES
    if not bank_holidays.is_work_day(date_to_check, division=area):
        # Ignore non working days
        return False

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
    cut_off_start_date = \
        calculate_working_day_date(cut_off_end_date, PAY_CUT_OFF_INTERVAL)
    return cut_off_start_date <= date_to_check <= cut_off_end_date
