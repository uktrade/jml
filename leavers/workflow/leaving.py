from django.conf import settings
from django_workflow_engine import Step, Workflow

from leavers.workflow.tasks import (  # noqa F401
    SECURITY_TEAM_BP_REMINDER_EMAILS,
    SECURITY_TEAM_RK_REMINDER_EMAILS,
    SRE_REMINDER_EMAILS,
    BasicTask,
    EmailIds,
    SkipCondition,
)

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
                "check_uksbs_leaver",
            ],
        ),
        Step(
            step_id="check_uksbs_leaver",
            task_name="check_uksbs_leaver",
            targets=[
                "send_leaver_not_in_uksbs_reminder",
                "check_uksbs_line_manager",
            ],
        ),
        Step(
            step_id="send_leaver_not_in_uksbs_reminder",
            task_name="reminder_email",
            targets=[
                "check_uksbs_leaver",
            ],
            task_info={
                "email_id": EmailIds.LINE_MANAGER_CORRECTION.value,
            },
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
        # Line Manager
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
                "setup_scheduled_tasks",
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
                "send_security_bp_notification",
                "send_security_rk_notification",
                "send_sre_notification",
                "is_it_leaving_date_plus_x",
            ],
        ),
        # UK SBS
        Step(
            step_id="send_uksbs_leaver_details",
            task_name="send_uksbs_leaver_details",
            targets=[
                "are_all_tasks_complete",
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
                "skip_condition": SkipCondition.USER_DOES_NOT_HAVE_OAB_LOCKER.value,
                "email_id": EmailIds.OCS_OAB_LOCKER_EMAIL.value,
            },
        ),
        # SECURITY (Building Pass)
        Step(
            step_id="send_security_bp_notification",
            task_name="notification_email",
            targets=[
                "have_security_carried_out_bp_leaving_tasks",
            ],
            task_info={
                "email_id": EmailIds.SECURITY_OFFBOARD_BP_LEAVER_NOTIFICATION.value,
            },
        ),
        Step(
            step_id="have_security_carried_out_bp_leaving_tasks",
            task_name="have_security_carried_out_bp_leaving_tasks",
            targets=[
                "send_security_bp_reminder",
                "are_all_tasks_complete",
            ],
        ),
        Step(
            step_id="send_security_bp_reminder",
            task_name="processor_reminder_email",
            targets=[
                "have_security_carried_out_bp_leaving_tasks",
            ],
            task_info={
                "processor_email": settings.SECURITY_TEAM_EMAIL,
                **SECURITY_TEAM_BP_REMINDER_EMAILS,
            },
        ),
        # SECURITY (ROSA Kit)
        Step(
            step_id="send_security_rk_notification",
            task_name="notification_email",
            targets=[
                "have_security_carried_out_rk_leaving_tasks",
            ],
            task_info={
                "email_id": EmailIds.SECURITY_OFFBOARD_RK_LEAVER_NOTIFICATION.value,
                "skip_condition": SkipCondition.IS_NOT_ROSA_USER.value,
            },
        ),
        Step(
            step_id="have_security_carried_out_rk_leaving_tasks",
            task_name="have_security_carried_out_rk_leaving_tasks",
            targets=[
                "send_security_rk_reminder",
                "are_all_tasks_complete",
            ],
        ),
        Step(
            step_id="send_security_rk_reminder",
            task_name="processor_reminder_email",
            targets=[
                "have_security_carried_out_rk_leaving_tasks",
            ],
            task_info={
                "skip_condition": SkipCondition.IS_NOT_ROSA_USER.value,
                "processor_email": settings.SECURITY_TEAM_EMAIL,
                **SECURITY_TEAM_RK_REMINDER_EMAILS,
            },
        ),
        # SRE (Slack)
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
                "are_all_tasks_complete",
            ],
        ),
        # SRE (Emails)
        Step(
            step_id="send_sre_notification",
            task_name="notification_email",
            targets=[
                "have_sre_carried_out_leaving_tasks",
            ],
            task_info={
                "email_id": EmailIds.SRE_NOTIFICATION.value,
            },
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
            task_name="processor_reminder_email",
            targets=[
                "have_sre_carried_out_leaving_tasks",
            ],
            task_info={
                "processor_email": settings.SRE_EMAIL,
                **SRE_REMINDER_EMAILS,
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
