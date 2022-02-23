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


notification_client = NotificationsAPIClient(
    settings.GOVUK_NOTIFY_API_KEY,
)


def email(email_address: str, template_id: EmailTemplates, personalisation: Dict):
    message_response = notification_client.send_email_notification(
        email_address=email_address,
        template_id=template_id.value,
        personalisation=personalisation,
    )

    return message_response
