from django_workflow_engine import Step, Workflow

from leavers.workflow.tasks import BasicTask  # noqa F401  # /PS-IGNORE

LeaversWorkflow = Workflow(
    name="leaving",
    steps=[
        Step(
            step_id="setup_leaving",
            task_name="basic_task",
            start=True,
            targets=[
                "notify_leaver",
            ],
        ),
        Step(
            step_id="notify_leaver",
            task_name="notification_email",
            targets=[
                "notify_line_manager",
            ],
            task_info={
                "subject": "Thank you for registering ",
                "message": "TODO - details of the leaver",
                "from_email": "noreply@jml.uktrade.com",  # /PS-IGNORE
            },
        ),
        Step(
            step_id="notify_line_manager",
            task_name="notification_email",
            targets=[
                "notify_hr_of_leaving",
            ],
            task_info={
                "subject": "Thank you for registering ",
                "message": "TODO - details of the leaver",
                "from_email": "noreply@jml.uktrade.com",  # /PS-IGNORE
            },
        ),
        Step(
            step_id="notify_hr_of_leaving",
            task_name="notification_email",
            targets=[
                "setup_scheduled_tasks",
            ],
            task_info={
                "groups": [
                    "HR",
                ],
                "subject": "A member of staff is leaving DIT",
                "message": "TODO - details of the leaver",
                "from_email": "noreply@jml.uktrade.com",  # /PS-IGNORE
            },
        ),
        # Split flow
        Step(
            step_id="setup_scheduled_tasks",
            task_name="basic_task",
            targets=[
                "is_it_leaving_date_plus_x",
                "is_it_x_days_before_payroll",
            ],
        ),
        # SRE
        Step(
            step_id="is_it_leaving_date_plus_x",
            task_name="is_it_leaving_date_plus_x",
            targets=[
                "send_sre_slack_message",
            ],
            break_flow=True,
        ),
        Step(
            step_id="send_sre_slack_message",
            task_name="send_sre_slack_message",
            targets=[
                "have_sre_carried_out_leaving_tasks",
            ],
        ),
        Step(
            step_id="have_sre_carried_out_leaving_tasks",
            task_name="have_sre_carried_out_leaving_tasks",
            targets=[
                "send_sre_reminder",
                "are_all_tasks_complete",
            ],
        ),
        Step(
            step_id="send_sre_reminder",
            task_name="notification_email",
            targets=[
                "have_sre_carried_out_leaving_tasks",
            ],
            task_info={
                "groups": [
                    "SRE",
                ],
                "subject": "Test",
                "message": "Please review the hardware required http://localhost:8000/{{ flow.continue_url }}.",  # noqa E501
                "from_email": "system@example.com",  # /PS-IGNORE
            },
            break_flow=True,
        ),
        # HR
        Step(
            step_id="is_it_x_days_before_payroll",
            task_name="is_it_x_days_before_payroll",
            targets=[
                "ask_hr_to_confirm_leaving_tasks",
            ],
            break_flow=True,
        ),
        Step(
            step_id="ask_hr_to_confirm_leaving_tasks",
            task_name="notification_email",
            targets=[
                "have_hr_carried_out_leaving_tasks",
            ],
            task_info={
                "groups": [
                    "HR",
                ],
                "subject": "Please confirm leaving tasks have been carried out",
                "message": "Please confirm you have carried out leaving tasks for {} here http://localhost:8000/{{ flow.continue_url }}.",  # noqa E501
                "from_email": "noreply@jml.uktrade.com",  # /PS-IGNORE
            },
        ),
        Step(
            step_id="have_hr_carried_out_leaving_tasks",
            task_name="have_hr_carried_out_leaving_tasks",
            targets=[
                "send_hr_reminder",
                "are_all_tasks_complete",
            ],
        ),
        Step(
            step_id="send_hr_reminder",
            task_name="notification_email",
            targets=[
                "have_hr_carried_out_leaving_tasks",
            ],
            task_info={
                "groups": [
                    "SRE",
                ],
                "subject": "Test",
                "message": "Please review the hardware required http://localhost:8000/{{ flow.continue_url }}.",  # noqa E501
                "from_email": "system@example.com",  # /PS-IGNORE
            },
            break_flow=True,
        ),
        Step(
            step_id="are_all_tasks_complete",
            task_name="basic_task",
            targets=[],
        ),
    ],
)
