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
            task_name="basic_task",
            start=True,
            targets=[
                "send_leaver_thank_you_email",
            ],
        ),
        Step(
            step_id="send_leaver_thank_you_email",
            task_name="notification_email",
            targets=[
                "send_leaver_questionnaire_email",
            ],
            task_info={
                "email_id": EmailIds.LEAVER_THANK_YOU_EMAIL.value,
            },
        ),
        Step(
            step_id="send_leaver_questionnaire_email",
            task_name="notification_email",
            targets=[
                "check_uksbs_leaver",
            ],
            task_info={
                "email_id": EmailIds.LEAVER_QUESTIONNAIRE_EMAIL.value,
            },
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
            task_name="daily_reminder_email",
            targets=[
                "check_uksbs_leaver",
            ],
            task_info={
                "email_id": EmailIds.LEAVER_NOT_IN_UKSBS_REMINDER.value,
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
            task_name="daily_reminder_email",
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
            task_name="basic_task",
            targets=[
                "send_uksbs_leaver_details",
                "send_service_now_leaver_details",
                "send_feetham_leaver_details",
                "send_it_ops_leaver_details",
                "send_lsd_team_leaver_details",
                "notify_clu4_of_leaving",
                "notify_ocs_of_leaving",
                "notify_ocs_of_oab_locker",
                "notify_health_and_safety",
                "should_notify_comaea_team",
                "notify_business_continuity_team",
                "send_security_bp_notification",
                "send_security_rk_notification",
                "have_sre_carried_out_leaving_tasks",
                "has_line_manager_updated_service_now",
            ],
        ),
        # UK SBS
        Step(
            step_id="send_uksbs_leaver_details",
            task_name="send_uksbs_leaver_details",
            targets=[
                "are_all_tasks_complete",
            ],
            task_info={
                "skip_conditions": [
                    SkipCondition.IS_TRANSFER.value,
                    SkipCondition.MANUALLY_OFFBOARDED_FROM_UKSBS.value,
                ],
            },
        ),
        # Service Now
        Step(
            step_id="send_service_now_leaver_details",
            task_name="send_service_now_leaver_details",
            targets=[
                "are_all_tasks_complete",
            ],
        ),
        # Feetham Security Pass Office
        Step(
            step_id="send_feetham_leaver_details",
            task_name="notification_email",
            targets=[
                "are_all_tasks_complete",
            ],
            task_info={
                "email_id": EmailIds.FEETHAM_SECURITY_PASS_OFFICE_EMAIL.value,
            },
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
        # CLU4
        Step(
            step_id="notify_clu4_of_leaving",
            task_name="notification_email",
            targets=[
                "are_all_tasks_complete",
            ],
            task_info={
                "email_id": EmailIds.CLU4_EMAIL.value,
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
        # Health and Safety or Floor Liaison officer
        Step(
            step_id="notify_health_and_safety",
            task_name="notification_email",
            targets=[
                "are_all_tasks_complete",
            ],
            task_info={
                "email_id": EmailIds.HEALTH_AND_SAFETY_EMAIL.value,
                "skip_conditions": [SkipCondition.IS_NOT_HSFL_LEAVER.value],
            },
        ),
        # COMAEA team
        Step(
            step_id="should_notify_comaea_team",
            task_name="pause_task",
            targets=[
                "notify_comaea_team",
            ],
            task_info={
                "pass_condition": "after_leaving_date",
            },
        ),
        Step(
            step_id="notify_comaea_team",
            task_name="notification_email",
            targets=[
                "are_all_tasks_complete",
            ],
            task_info={
                "email_id": EmailIds.COMAEA_EMAIL.value,
            },
        ),
        # Business Continuity
        Step(
            step_id="notify_business_continuity_team",
            task_name="notification_email",
            targets=[
                "are_all_tasks_complete",
            ],
            task_info={
                "email_id": EmailIds.BUISNESS_CONTINUITY_LEAVER_EMAIL.value,
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
                "processor_emails": [settings.SECURITY_TEAM_BUILDING_PASS_EMAIL],
                **SECURITY_TEAM_BP_REMINDER_EMAILS,  # type: ignore
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
                "skip_conditions": [SkipCondition.IS_NOT_ROSA_USER.value],
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
                "skip_conditions": [SkipCondition.IS_NOT_ROSA_USER.value],
                "processor_emails": [settings.SECURITY_TEAM_ROSA_EMAIL],
                **SECURITY_TEAM_RK_REMINDER_EMAILS,  # type: ignore
            },
        ),
        # Line manager
        Step(
            step_id="has_line_manager_updated_service_now",
            task_name="has_line_manager_updated_service_now",
            targets=[
                "send_line_manager_offline_service_now_reminder",
                "are_all_tasks_complete",
            ],
        ),
        Step(
            step_id="send_line_manager_offline_service_now_reminder",
            task_name="daily_reminder_email",
            targets=[
                "has_line_manager_updated_service_now",
            ],
            task_info={
                "email_id": EmailIds.LINE_MANAGER_OFFLINE_SERVICE_NOW.value,
            },
        ),
        # SRE (Emails & Slack)
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
                "processor_emails": [settings.SRE_EMAIL],
                **SRE_REMINDER_EMAILS,  # type: ignore
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
