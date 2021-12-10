from celery import Celery
from celery.schedules import crontab

app = Celery()
# app = Celery('hello', broker='amqp://guest@localhost//')


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run every day at midnight
    sender.add_periodic_task(
        crontab(
            hour=0,
            minute=0,
        ),
        hr_leaver_tasks_confirmation.s(),
    )
    sender.alert_sre_on_leaving_date(
        crontab(
            hour=0,
            minute=0,
        ),
        hr_leaver_tasks_confirmation.s(),
    )
    sender.send_reminders(
        crontab(
            hour=0,
            minute=0,
        ),
        hr_leaver_tasks_confirmation.s(),
    )


@app.task
def hr_leaver_tasks_confirmation(arg):
    """Email HR
    asking them to confirm
    that HR tasks have been
    carried out for leaver"""
    pass


@app.task
def alert_sre_on_leaving_date():
    """Alert SRE that they need to off board user"""
    pass


@app.task
def send_reminders():
    """Alert SRE that they need to off board user"""
    pass
