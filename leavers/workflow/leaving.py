from django_workflow_engine import Step, Workflow

from leavers.workflow.tasks import BasicTask, EmailIds  # noqa F401

"""
Leavers Workflow

This can be triggered in 2 places:
- By the Leaver when they notify the Service that they are leaving
- By the Leaver Reporter when they notify the Service that there is a Leaver
"""

LeaversWorkflow = Workflow(
    name="leaving",
    steps=[
        # Leaver
        Step(
            step_id="setup_leaving",
            task_name="confirm_leaver_data",
            start=True,
            targets=[
                "check_uksbs_line_manager",
            ],
        ),
        Step(
            step_id="check_uksbs_line_manager",
            task_name="check_uksbs_line_manager",
            targets=[
                "send_line_manager_correction_reminder",
                "notify_line_manager",
            ],
        ),
        Step(
            step_id="send_line_manager_correction_reminder",
            task_name="reminder_email",
            targets=[
                "check_uksbs_line_manager",
            ],
            task_info={
                "email_id": EmailIds.LINE_MANAGER_CORRECTION.value,
            },
        ),
        # Line manager
        Step(
            step_id="notify_line_manager",
            task_name="notification_email",
            targets=[
                "has_line_manager_completed",
            ],
            task_info={
                "email_id": EmailIds.LINE_MANAGER_NOTIFICATION.value,
            },
        ),
        Step(
            step_id="has_line_manager_completed",
            task_name="has_line_manager_completed",
            targets=[
                "send_line_manager_reminder",
                "thank_line_manager",
            ],
        ),
        Step(
            step_id="send_line_manager_reminder",
            task_name="reminder_email",
            targets=[
                "has_line_manager_completed",
            ],
            task_info={
                "email_id": EmailIds.LINE_MANAGER_REMINDER.value,
            },
        ),
        Step(
            step_id="thank_line_manager",
            task_name="notification_email",
            targets=[
                "send_uksbs_leaver_details",
            ],
            task_info={
                "email_id": EmailIds.LINE_MANAGER_THANKYOU.value,
            },
        ),
        # Split flow
        Step(
            step_id="setup_scheduled_tasks",
            task_name="pause_task",  # TODO: Swap back to basic_task
            targets=[
                "send_uksbs_leaver_details",
                "send_service_now_leaver_details",
                "send_it_ops_leaver_details",
                "send_lsd_team_leaver_details",
                "notify_csu4_of_leaving",
                "notify_ocs_of_leaving",
                "notify_ocs_of_oab_locker",
                "send_security_notification",
                "is_it_leaving_date_plus_x",
            ],
        ),
        # UK SBS
        Step(
            step_id="send_uksbs_leaver_details",
            task_name="send_uksbs_leaver_details",
            targets=[
                "setup_scheduled_tasks",
            ],
        ),
        # Service Now
        Step(
            step_id="send_service_now_leaver_details",
            task_name="send_service_now_leaver_details",
            targets=[
                "are_all_tasks_complete",
            ],
        ),
        # IT Ops
        Step(
            step_id="send_it_ops_leaver_details",
            task_name="notification_email",
            targets=[
                "are_all_tasks_complete",
            ],
            task_info={
                "email_id": EmailIds.IT_OPS_ASSET_EMAIL.value,
            },
        ),
        # LSD
        Step(
            step_id="send_lsd_team_leaver_details",
            task_name="send_lsd_team_leaver_details",
            targets=[
                "are_all_tasks_complete",
            ],
        ),
        # CSU4
        Step(
            step_id="notify_csu4_of_leaving",
            task_name="notification_email",
            targets=[
                "are_all_tasks_complete",
            ],
            task_info={
                "email_id": EmailIds.CSU4_EMAIL.value,
            },
        ),
        # OCS
        Step(
            step_id="notify_ocs_of_leaving",
            task_name="notification_email",
            targets=[
                "are_all_tasks_complete",
            ],
            task_info={
                "email_id": EmailIds.OCS_EMAIL.value,
            },
        ),
        # OCS OAB Lockers
        Step(
            step_id="notify_ocs_of_oab_locker",
            task_name="notification_email",
            targets=[
                "are_all_tasks_complete",
            ],
            task_info={
                "email_id": EmailIds.OCS_OAB_LOCKER_EMAIL.value,
            },
        ),
        # SECURITY
        Step(
            step_id="send_security_notification",
            task_name="notification_email",
            targets=[
                "have_security_carried_out_leaving_tasks",
            ],
            task_info={
                "email_id": EmailIds.SECURITY_OFFBOARD_LEAVER_NOTIFICATION.value,
            },
        ),
        Step(
            step_id="have_security_carried_out_leaving_tasks",
            task_name="have_security_carried_out_leaving_tasks",
            targets=[
                "send_security_reminder",
                "are_all_tasks_complete",
            ],
        ),
        Step(
            step_id="send_security_reminder",
            task_name="reminder_email",
            targets=[
                "have_security_carried_out_leaving_tasks",
            ],
            task_info={
                "email_id": EmailIds.SECURITY_OFFBOARD_LEAVER_REMINDER.value,
            },
        ),
        # SRE
        Step(
            step_id="is_it_leaving_date_plus_x",
            task_name="is_it_leaving_date_plus_x",
            targets=[
                "send_sre_slack_message",
            ],
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
            task_name="reminder_email",
            targets=[
                "have_sre_carried_out_leaving_tasks",
            ],
            task_info={
                "email_id": EmailIds.SRE_REMINDER.value,
            },
        ),
        # End
        Step(
            step_id="are_all_tasks_complete",
            task_name="leaver_complete",
            targets=[],
        ),
    ],
)
