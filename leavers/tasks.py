from celery import shared_task
from config.celery import celery_app
from datetime import date
from leavers.models import LeavingRequest
from leavers.utils.emails import send_leaver_list_pay_cut_off_reminder
from leavers.utils.workday_calculation import is_date_within_payroll_cutoff_interval

logger = celery_app.log.get_default_logger()


@shared_task()
def notify_hr(date_to_check=date.today()):
    logger.info("RUNNING task_notify_hr")
    is_within, cut_off_date = is_date_within_payroll_cutoff_interval(date_to_check)
    if is_within:
        logger.info(
            f"Today {date_to_check} within cut off period ending on {cut_off_date}"
        )
        # Check if there are incomplete leavers with leaving date
        # before or on the cutoff date
        # All leavers are included, ie contractors and civil servants
        leavers_incomplete_qs = LeavingRequest.objects.filter(
            line_manager_complete__isnull=True,
            leaving_date__date__lte=cut_off_date,
        )
        if leavers_incomplete_qs.count():
            logger.info(f"Found {leavers_incomplete_qs.count()} uncomplete leavers")
            # Email the list to HR
            send_leaver_list_pay_cut_off_reminder(leavers_incomplete_qs)
        else:
            logger.info("Found no uncomplete leavers")
