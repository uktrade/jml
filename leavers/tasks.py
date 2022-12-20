from datetime import date
from leavers.models import LeavingRequest

from leavers.utils.workday_calculation import (
    is_date_within_payroll_cutoff_interval,
)

def task_notify_hr():
    is_within, cut_off_date =  is_date_within_payroll_cutoff_interval(date.today())
    if is_within:
        # Check if there are incomplete leavers with leaving date
        # before or on the cutoff date
        leavers_incomplete_qs = LeavingRequest.objects.filter(
            line_manager_complete__isnull=True,
            leaving_date__date__lte=cut_off_date
        )
        if leavers_incomplete_qs.count():
        # Email the list to HR
            pass
