from enum import Enum
from typing import Dict, List

from django.conf import settings
from notifications_python_client.notifications import NotificationsAPIClient


class EmailTemplates(Enum):
    """
    GOV.UK Notify email Templates.
    """

    LEAVER_THANK_YOU_EMAIL = settings.TEMPLATE_ID_LEAVER_THANK_YOU_EMAIL
    LEAVER_NOT_IN_UKSBS_HR_REMINDER = (
        settings.TEMPLATE_ID_LEAVER_NOT_IN_UKSBS_HR_REMINDER
    )
    LEAVER_NOT_IN_UKSBS_LM_REMINDER = (
        settings.TEMPLATE_ID_LEAVER_NOT_IN_UKSBS_LM_REMINDER
    )
    LINE_MANAGER_CORRECTION_EMAIL = settings.TEMPLATE_ID_LINE_MANAGER_CORRECTION_EMAIL
    LINE_MANAGER_CORRECTION_HR_EMAIL = (
        settings.TEMPLATE_ID_LINE_MANAGER_CORRECTION_HR_EMAIL
    )
    LINE_MANAGER_CORRECTION_REPORTED_LM_EMAIL = (
        settings.TEMPLATE_ID_LINE_MANAGER_CORRECTION_REPORTED_LM_EMAIL
    )
    LINE_MANAGER_NOTIFICATION_EMAIL = (
        settings.TEMPLATE_ID_LINE_MANAGER_NOTIFICATION_EMAIL
    )
    LINE_MANAGER_REMINDER_EMAIL = settings.TEMPLATE_ID_LINE_MANAGER_REMINDER_EMAIL
    LINE_MANAGER_THANKYOU_EMAIL = settings.TEMPLATE_ID_LINE_MANAGER_THANKYOU_EMAIL
    CSU4_LEAVER_EMAIL = settings.TEMPLATE_ID_CSU4_EMAIL
    IT_OPS_ASSET_EMAIL = settings.TEMPLATE_ID_IT_OPS_ASSET_EMAIL
    OCS_LEAVER_EMAIL = settings.TEMPLATE_ID_OCS_LEAVER_EMAIL
    OCS_OAB_LOCKER_EMAIL = settings.TEMPLATE_ID_OCS_OAB_LOCKER_EMAIL
    SECURITY_TEAM_OFFBOARD_BP_LEAVER_EMAIL = (
        settings.TEMPLATE_ID_SECURITY_TEAM_OFFBOARD_BP_LEAVER_EMAIL
    )
    SECURITY_TEAM_OFFBOARD_RK_LEAVER_EMAIL = (
        settings.TEMPLATE_ID_SECURITY_TEAM_OFFBOARD_RK_LEAVER_EMAIL
    )
    SRE_REMINDER_EMAIL = settings.TEMPLATE_ID_SRE_REMINDER_EMAIL


def email(
    email_addresses: List[str], template_id: EmailTemplates, personalisation: Dict
):
    notification_client = NotificationsAPIClient(
        settings.GOVUK_NOTIFY_API_KEY,
    )

    # Send all emails to the JML team
    if settings.PROCESS_LEAVING_REQUEST:
        email_addresses += settings.JML_TEAM_EMAILS
    else:
        email_addresses = settings.JML_TEAM_EMAILS

    for email_address in email_addresses:
        message_response = notification_client.send_email_notification(
            email_address=email_address,
            template_id=template_id.value,
            personalisation=personalisation,
        )

    return message_response
