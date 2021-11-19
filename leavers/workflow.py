from django import forms
from django_workflow_engine import Step, Workflow

from leavers.models import LeavingRequest
from leavers.tasks import CreateLeavingRequest, SetupLeaving

LeaversWorkflow = Workflow(
    name="leaving",
    steps=[
        Step(
            step_id="setup_leaving",
            task_name="setup_leaving",
            start=True,
            target="create_leaving_request",
        ),
        Step(
            step_id="create_leaving_request",
            task_name="create_leaving_request",
            target="sre_confirm_tasks_complete",
        ),
        # Step(
        #     step_id="send_sre_slack_message",
        #     task_name="send_sre_slack_message",
        #     target="sre_confirm_tasks_complete",
        # ),
        Step(
            step_id="sre_confirm_tasks_complete",
            task_name="sre_confirm_tasks_complete",
            target=None,
            # groups=[
            #     "SRE",
            # ]
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
