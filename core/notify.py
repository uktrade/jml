from enum import Enum
from typing import Dict

from django.conf import settings
from notifications_python_client.notifications import NotificationsAPIClient


class EmailTemplates(Enum):
    """
    GOV.UK Notify email Templates.
    """

    CSU4_LEAVER_EMAIL = settings.CSU4_EMAIL_TEMPLATE_ID
    OCS_LEAVER_EMAIL = settings.OCS_LEAVER_EMAIL_TEMPLATE_ID
    ROSA_LEAVER_REMINDER_EMAIL = settings.ROSA_LEAVER_REMINDER_EMAIL
    ROSA_LINE_MANAGER_REMINDER_EMAIL = settings.ROSA_LINE_MANAGER_REMINDER_EMAIL
    SECURITY_TEAM_OFFBOARD_LEAVER_EMAIL = settings.SECURITY_TEAM_OFFBOARD_LEAVER_EMAIL
    SECURITY_TEAM_OFFBOARD_LEAVER_REMINDER_EMAIL = (
        settings.SECURITY_TEAM_OFFBOARD_LEAVER_REMINDER_EMAIL
    )
    LINE_MANAGER_NOTIFICATION_EMAIL = settings.LINE_MANAGER_NOTIFICATION_EMAIL
    LINE_MANAGER_REMINDER_EMAIL = settings.LINE_MANAGER_REMINDER_EMAIL
    LINE_MANAGER_THANKYOU_EMAIL = settings.LINE_MANAGER_THANKYOU_EMAIL
    SRE_REMINDER_EMAIL = settings.SRE_REMINDER_EMAIL


def email(email_address: str, template_id: EmailTemplates, personalisation: Dict):
    # TODO: Test GOV UK Notify Integration
    notification_client = NotificationsAPIClient(
        settings.GOVUK_NOTIFY_API_KEY,
    )

    message_response = notification_client.send_email_notification(
        email_address=email_address,
        template_id=template_id.value,
        personalisation=personalisation,
    )

    return message_response
