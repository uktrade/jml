from datetime import date, timedelta
from govuk_bank_holidays.bank_holidays import BankHolidays

PAY_CUT_OFF_DAY = 3  # The third of the month is the designated cutoff date
ALTERNATIVE_WEEK_DAY_DESIGNATED = 4  # Friday
PAY_CUT_OFF_INTERVAL = 4


def working_day_delta(start_date: date, working_day_delta: int) -> date:
    bank_holidays = BankHolidays()
    area = BankHolidays.ENGLAND_AND_WALES
    new_date = start_date
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

    # Find the designated day, in this case the previous Friday
    cut_off_day_of_week = cutoff_day.weekday()
    delta = cut_off_day_of_week - ALTERNATIVE_WEEK_DAY_DESIGNATED
    if delta <= 0:
        delta += 7
    cutoff_day -= timedelta(delta)
    # If the previous designated day is also a bankholiday,
    # return the previous working day
    while not bank_holidays.is_work_day(cutoff_day, division=area):
        cutoff_day -= timedelta(-1)
    return cutoff_day


def is_date_within_payroll_cutoff(date_to_check: date) -> bool:
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
        if month_to_check == 12:
            # Special case for December
            next_month = 1
            year_to_check += 1
        else:
            next_month = month_to_check + 1
        cut_off_end_date = pay_cut_off_date(next_month, year_to_check)
    cut_off_start_date = working_day_delta(cut_off_end_date, PAY_CUT_OFF_INTERVAL)
    return cut_off_start_date <= date_to_check <= cut_off_end_date
