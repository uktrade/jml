from django_workflow_engine import Workflow, Step
# from celery.schedules import crontab

from leavers.workflow.util import (
    is_leaving_date,
    is_x_days_before_payroll,
)


LeaversWorkflow = Workflow(
    name="leaving",
    steps=[
        Step(
            step_id="setup_leaving",
            task_name="setup_leaving",
            start=True,
            target="sre_confirm_tasks_complete",
        ),
        Step(
            step_id="find_group_recipients",
            task_name="find_group_recipients",
            target="alert_hardware_team",
            task_info={
                "group_name": "HR",
            },
        ),
        Step(
            step_id="email_hr",
            task_name="send_email",
            target="hr_confirmation_email",
            task_info={
                "subject": "A member of staff is leaving DIT",
                "message": "TODO - details of the leaver",
                "from_email": "noreply@jml.uktrade.com",
            },
        ),
        Step(
            step_id="hr_confirmation_email",
            task_name="send_email",
            target="hr_confirm_leaving_tasks",
            condition=is_x_days_before_payroll,
            task_info={
                "subject": "Please confirm leaving tasks have been carried out",
                "message": "Please confirm you have carried out leaving tasks for {} here http://localhost:8000/{{ flow.continue_url }}.",
                "from_email": "noreply@jml.uktrade.com",
            },
        ),
        Step(
            step_id="hr_confirm_leaving_tasks",
            task_name="hr_confirm_leaving_tasks",
            target="hr_confirm_tasks_carried_out_email",
            # groups=[
            #     "HR",
            # ]
            reminder=crontab(hour=0, minute=0,),
            #     reminder_info={
            #         "subject": "This is a gentle reminder to confirm leaving tasks for x",
            #         "message": "Please confirm that you have carried out leaving tasks for x here http://localhost:8000/{{ flow.continue_url }}",
            #         "from_email": "noreply@jml.uktrade.com",
            #     },
        ),
        Step(  # Record that HR leaving tasks have been carried out
            step_id="hr_confirm_tasks_carried_out",
            target="send_sre_slack_message",
            condition=is_x_days_before_payroll,
        ),
        Step(
            step_id="send_sre_slack_message",
            task_name="send_sre_slack_message",
            target="sre_confirm_tasks_complete",
            condition=is_leaving_date,
        ),
        Step(
            step_id="sre_confirm_tasks_complete",
            task_name="sre_confirm_tasks_complete",
            target=None,
            reminder=crontab(hour=0, minute=0,),
            # groups=[
            #     "SRE",
            # ]
            #     reminder_info={
            #         "subject": "Test",
            #         "message": "Please review the hardware required http://localhost:8000/{{ flow.continue_url }}.",
            #         "from_email": "system@example.com",
            #     },
        ),
        # Step(
        #     step_id="find_group_recipients",
        #     task_name="find_group_recipients",
        #     target="alert_hardware_team",
        #     task_info={
        #         "group_name": "Hardware Team",
        #     },
        # ),
        # Step(
        #     step_id="alert_hardware_team",
        #     task_name="send_email",
        #     target="confirm_hardware_received",
        #     task_info={
        #         "subject": "Test",
        #         "message": "Please review the hardware required http://localhost:8000/{{ flow.continue_url }}.",
        #         "from_email": "system@example.com",
        #     },
        # ),
        # Step(
        #     step_id="confirm_hardware_received",
        #     task_name="confirm_hardware_received",
        #     target=None,
        #     groups=[
        #         "Hardware Team",
        #     ]
        # ),
    ],
)
