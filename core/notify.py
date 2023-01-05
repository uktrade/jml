from enum import Enum
from typing import Dict, List

from django.conf import settings
from notifications_python_client.notifications import NotificationsAPIClient

from leavers.settings import email_template_settings


class EmailTemplates(Enum):
    """
    GOV.UK Notify email Templates.
    """

    LEAVER_THANK_YOU_EMAIL = email_template_settings.LEAVER_THANK_YOU_EMAIL
    LEAVER_NOT_IN_UKSBS_HR_REMINDER = (
        email_template_settings.LEAVER_NOT_IN_UKSBS_HR_REMINDER
    )
    LEAVER_NOT_IN_UKSBS_LM_REMINDER = (
        email_template_settings.LEAVER_NOT_IN_UKSBS_LM_REMINDER
    )
    LINE_MANAGER_CORRECTION_EMAIL = (
        email_template_settings.LINE_MANAGER_CORRECTION_EMAIL
    )
    LINE_MANAGER_CORRECTION_HR_EMAIL = (
        email_template_settings.LINE_MANAGER_CORRECTION_HR_EMAIL
    )
    LINE_MANAGER_CORRECTION_REPORTED_LM_EMAIL = (
        email_template_settings.LINE_MANAGER_CORRECTION_REPORTED_LM_EMAIL
    )
    LINE_MANAGER_NOTIFICATION_EMAIL = (
        email_template_settings.LINE_MANAGER_NOTIFICATION_EMAIL
    )
    LINE_MANAGER_REMINDER_EMAIL = email_template_settings.LINE_MANAGER_REMINDER_EMAIL
    LINE_MANAGER_THANKYOU_EMAIL = email_template_settings.LINE_MANAGER_THANKYOU_EMAIL
    LINE_MANAGER_OFFLINE_SERVICE_NOW_EMAIL = (
        email_template_settings.LINE_MANAGER_OFFLINE_SERVICE_NOW_EMAIL
    )

    CLU4_LEAVER_EMAIL = email_template_settings.CLU4_EMAIL
    FEETHAM_SECURITY_PASS_OFFICE_EMAIL = (
        email_template_settings.FEETHAM_SECURITY_PASS_OFFICE_EMAIL
    )
    IT_OPS_ASSET_EMAIL = email_template_settings.IT_OPS_ASSET_EMAIL
    OCS_LEAVER_EMAIL = email_template_settings.OCS_LEAVER_EMAIL
    OCS_OAB_LOCKER_EMAIL = email_template_settings.OCS_OAB_LOCKER_EMAIL
    COMAEA_EMAIL = email_template_settings.COMAEA_EMAIL

    SECURITY_TEAM_OFFBOARD_BP_LEAVER_EMAIL = (
        email_template_settings.SECURITY_TEAM_OFFBOARD_BP_LEAVER_EMAIL
    )
    SECURITY_OFFBOARD_BP_REMINDER_DAY_AFTER_LWD = (
        email_template_settings.SECURITY_OFFBOARD_BP_REMINDER_DAY_AFTER_LWD
    )
    SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LWD = (
        email_template_settings.SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LWD
    )
    SECURITY_OFFBOARD_BP_REMINDER_ON_LD = (
        email_template_settings.SECURITY_OFFBOARD_BP_REMINDER_ON_LD
    )
    SECURITY_OFFBOARD_BP_REMINDER_ONE_DAY_AFTER_LD = (
        email_template_settings.SECURITY_OFFBOARD_BP_REMINDER_ONE_DAY_AFTER_LD
    )
    SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_LM = (
        email_template_settings.SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_LM
    )
    SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_PROC = (
        email_template_settings.SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_PROC
    )

    SECURITY_TEAM_OFFBOARD_RK_LEAVER_EMAIL = (
        email_template_settings.SECURITY_TEAM_OFFBOARD_RK_LEAVER_EMAIL
    )
    SECURITY_OFFBOARD_RK_REMINDER_DAY_AFTER_LWD = (
        email_template_settings.SECURITY_OFFBOARD_RK_REMINDER_DAY_AFTER_LWD
    )
    SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LWD = (
        email_template_settings.SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LWD
    )
    SECURITY_OFFBOARD_RK_REMINDER_ON_LD = (
        email_template_settings.SECURITY_OFFBOARD_RK_REMINDER_ON_LD
    )
    SECURITY_OFFBOARD_RK_REMINDER_ONE_DAY_AFTER_LD = (
        email_template_settings.SECURITY_OFFBOARD_RK_REMINDER_ONE_DAY_AFTER_LD
    )
    SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LD_LM = (
        email_template_settings.SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LD_LM
    )
    SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LD_PROC = (
        email_template_settings.SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LD_PROC
    )

    SRE_NOTIFICATION = "no_template_id_we_send_slack_messages"
    SRE_REMINDER_DAY_AFTER_LWD = "no_template_id_we_send_slack_messages"
    SRE_REMINDER_ONE_DAY_AFTER_LD = "no_template_id_we_send_slack_messages"
    SRE_REMINDER_TWO_DAYS_AFTER_LD_PROC = "no_template_id_we_send_slack_messages"


def email(
    email_addresses: List[str], template_id: EmailTemplates, personalisation: Dict
):
    notification_client = NotificationsAPIClient(
        settings.GOVUK_NOTIFY_API_KEY,
    )

    # Send all emails to the JML team
    email_addresses += settings.JML_TEAM_EMAILS

    if settings.JML_ONLY_SEND_EMAILS_TO_JML_TEAM:
        email_addresses = settings.JML_TEAM_EMAILS

    for email_address in email_addresses:
        message_response = notification_client.send_email_notification(
            email_address=email_address,
            template_id=template_id.value,
            personalisation=personalisation,
        )

    return message_response
