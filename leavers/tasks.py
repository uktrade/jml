from datetime import date, timedelta
from typing import Optional

from config.celery import celery_app
from leavers.models import LeavingRequest
from leavers.utils.emails import (
    send_leaver_list_pay_cut_off_reminder,
    send_workforce_planning_leavers_email,
)
from leavers.utils.workday_calculation import is_date_within_payroll_cut_off_interval

logger = celery_app.log.get_default_logger()


@celery_app.task(bind=True)
def notify_hr(self, date_to_check: Optional[date] = None) -> None:
    if not date_to_check:
        date_to_check = date.today()

    logger.info(f"RUNNING notify_hr {date_to_check=}")
    is_within, cut_off_date = is_date_within_payroll_cut_off_interval(
        date_to_check=date_to_check,
    )
    if is_within:
        logger.info(
            f"Today {date_to_check} within cut off period ending on {cut_off_date}"
        )
        # Check if there are incomplete leavers with leaving date
        # before or on the cut off date
        # All leavers are included, ie contractors and civil servants
        leavers_incomplete_qs = LeavingRequest.objects.filter(
            cancelled__isnull=True,
            line_manager_complete__isnull=True,
            leaving_date__date__lte=cut_off_date,
        )
        if leavers_incomplete_qs.count():
            logger.info(f"Found {leavers_incomplete_qs.count()} incomplete leavers")
            # Email the list to HR
            send_leaver_list_pay_cut_off_reminder(leavers_incomplete_qs)
        else:
            logger.info("Found no incomplete leavers")


@celery_app.task(bind=True)
def weekly_leavers_email(self) -> None:
    # If today is monday
    if date.today().weekday() != 0:
        return None

    logger.info("RUNNING weekly_leavers_email")

    past_monday = date.today() - timedelta(days=7)
    past_sunday = date.today() - timedelta(days=1)
    leavers_last_week = LeavingRequest.objects.all().filter(
        cancelled__isnull=True,
        line_manager_complete__isnull=False,
        leaving_date__date__gte=past_monday,
        leaving_date__date__lte=past_sunday,
    )
    send_workforce_planning_leavers_email(
        leaving_requests=leavers_last_week,
        week_ending=past_sunday.strftime("%d/%m/%Y"),
    )
